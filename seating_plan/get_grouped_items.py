
import sys

from importlib import import_module
from unicodedata import category
from urllib.parse import urlencode


from django.conf import settings
from django.db.models import (
    Count, Exists, OuterRef, Prefetch, Q,
)

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, pgettext_lazy


from pretix.base.channels import get_all_sales_channels
from pretix.base.models import (
    ItemVariation, Quota
)

from pretix.base.models.items import (
    ItemBundle, SubEventItem, SubEventItemVariation,
)
from pretix.base.services.quotas import QuotaAvailability

from pretix.presale.signals import item_description



def item_group_by_category(items):
    return sorted(
        [
            # a group is a tuple of a category and a list of items
            (cat, [i for i in items if i.category == cat])
            for cat in set([i.category for i in items])
            # insert categories into a set for uniqueness
            # a set is unsorted, so sort again by category
        ],
        key=lambda group: (group[0].position, group[0].id) if (
            group[0] is not None and group[0].id is not None) else (0, 0)
    )



def get_grouped_items(event, subevent=None, voucher=None, channel='web', require_seat=0, base_qs=None, allow_addons=False,
                      quota_cache=None, filter_items=None, filter_categories=None, memberships=None,
                      ignore_hide_sold_out_for_item_ids=None):
    base_qs_set = base_qs is not None
    base_qs = base_qs if base_qs is not None else event.items
    print(base_qs)
 
    variation_q = (
        Q(Q(available_from__isnull=True) | Q(available_from__lte=now())) &
        Q(Q(available_until__isnull=True) | Q(available_until__gte=now()))
    )
    if not voucher or not voucher.show_hidden_items:
        variation_q &= Q(hide_without_voucher=False)

    if memberships is not None:
        prefetch_membership_types = ['require_membership_types']
    else:
        prefetch_membership_types = []

    items = base_qs.using(settings.DATABASE_REPLICA).filter_available(channel=channel, voucher=voucher, allow_addons=allow_addons).select_related(
        'category', 'tax_rule',  # for re-grouping
        'hidden_if_available',
    ).prefetch_related(
        *prefetch_membership_types,
        Prefetch('quotas',
                 to_attr='_subevent_quotas',
                 queryset=event.quotas.using(settings.DATABASE_REPLICA).filter(subevent=subevent)),
        Prefetch('bundles',
                 queryset=ItemBundle.objects.using(settings.DATABASE_REPLICA).prefetch_related(
                     Prefetch('bundled_item',
                              queryset=event.items.using(settings.DATABASE_REPLICA).select_related('tax_rule').prefetch_related(
                                  Prefetch('quotas',
                                           to_attr='_subevent_quotas',
                                           queryset=event.quotas.using(settings.DATABASE_REPLICA).filter(subevent=subevent)),
                              )),
                     Prefetch('bundled_variation',
                              queryset=ItemVariation.objects.using(
                                  settings.DATABASE_REPLICA
                              ).select_related('item', 'item__tax_rule').filter(item__event=event).prefetch_related(
                                  Prefetch('quotas',
                                           to_attr='_subevent_quotas',
                                           queryset=event.quotas.using(settings.DATABASE_REPLICA).filter(subevent=subevent)),
                              )),
                 )),
        Prefetch('variations', to_attr='available_variations',
                 queryset=ItemVariation.objects.using(settings.DATABASE_REPLICA).annotate(
                     subevent_disabled=Exists(
                         SubEventItemVariation.objects.filter(
                             Q(disabled=True) | Q(available_from__gt=now()) | Q(available_until__lt=now()),
                             variation_id=OuterRef('pk'),
                             subevent=subevent,
                         )
                     ),
                 ).filter(
                     variation_q,
                     active=True,
                     sales_channels__contains=channel,
                     quotas__isnull=False,
                     subevent_disabled=False
                 ).prefetch_related(
                     *prefetch_membership_types,
                     Prefetch('quotas',
                              to_attr='_subevent_quotas',
                              queryset=event.quotas.using(settings.DATABASE_REPLICA).filter(subevent=subevent))
                 ).distinct()),
    ).annotate(
        quotac=Count('quotas'),
        has_variations=Count('variations'),
        subevent_disabled=Exists(
            SubEventItem.objects.filter(
                Q(disabled=True) | Q(available_from__gt=now()) | Q(available_until__lt=now()),
                item_id=OuterRef('pk'),
                subevent=subevent,
            )
        )
    ).filter(
        quotac__gt=0, subevent_disabled=False,
    ).order_by('category__position', 'category_id', 'position', 'name')
    if require_seat:
        items = items.filter(requires_seat__gt=0)
    elif require_seat is not None:
        items = items.filter(requires_seat=0)

    if filter_items:
        items = items.filter(pk__in=[a for a in filter_items if a.isdigit()])
    if filter_categories:
        items = items.filter(category_id__in=[a for a in filter_categories if a.isdigit()])

    display_add_to_cart = False
    quota_cache_key = f'item_quota_cache:{subevent.id if subevent else 0}:{channel}:{bool(require_seat)}'
    quota_cache = quota_cache or event.cache.get(quota_cache_key) or {}
    quota_cache_existed = bool(quota_cache)

    if subevent:
        item_price_override = subevent.item_price_overrides
        var_price_override = subevent.var_price_overrides
    else:
        item_price_override = {}
        var_price_override = {}

    restrict_vars = set()
    if voucher and voucher.quota_id:
        # If a voucher is set to a specific quota, we need to filter out on that level
        restrict_vars = set(voucher.quota.variations.all())

    quotas_to_compute = []
    for item in items:
        if item.has_variations:
            for v in item.available_variations:
                for q in v._subevent_quotas:
                    if q.pk not in quota_cache:
                        quotas_to_compute.append(q)
        else:
            for q in item._subevent_quotas:
                if q.pk not in quota_cache:
                    quotas_to_compute.append(q)

    if quotas_to_compute:
        qa = QuotaAvailability()
        qa.queue(*quotas_to_compute)
        qa.compute()
        quota_cache.update({q.pk: r for q, r in qa.results.items()})

    for item in items:
        if voucher and voucher.item_id and voucher.variation_id:
            # Restrict variations if the voucher only allows one
            item.available_variations = [v for v in item.available_variations
                                         if v.pk == voucher.variation_id]

        if get_all_sales_channels()[channel].unlimited_items_per_order:
            max_per_order = sys.maxsize
        else:
            max_per_order = item.max_per_order or int(event.settings.max_items_per_order)

        if item.hidden_if_available:
            q = item.hidden_if_available.availability(_cache=quota_cache)
            if q[0] == Quota.AVAILABILITY_OK:
                item._remove = True
                continue

        if item.require_membership and item.require_membership_hidden:
            if not memberships or not any([m.membership_type in item.require_membership_types.all() for m in memberships]):
                item._remove = True
                continue

        item.description = str(item.description)
        for recv, resp in item_description.send(sender=event, item=item, variation=None):
            if resp:
                item.description += ("<br/>" if item.description else "") + resp

        if not item.has_variations:
            item._remove = False
            if not bool(item._subevent_quotas):
                item._remove = True
                continue

            if voucher and (voucher.allow_ignore_quota or voucher.block_quota):
                item.cached_availability = (
                    Quota.AVAILABILITY_OK, voucher.max_usages - voucher.redeemed
                )
            else:
                item.cached_availability = list(
                    item.check_quotas(subevent=subevent, _cache=quota_cache, include_bundled=True)
                )

            if not (
                    ignore_hide_sold_out_for_item_ids and item.pk in ignore_hide_sold_out_for_item_ids
            ) and event.settings.hide_sold_out and item.cached_availability[0] < Quota.AVAILABILITY_RESERVED:
                item._remove = True
                continue

            item.order_max = min(
                item.cached_availability[1]
                if item.cached_availability[1] is not None else sys.maxsize,
                max_per_order
            )

            original_price = item_price_override.get(item.pk, item.default_price)
            if voucher:
                price = voucher.calculate_price(original_price)
            else:
                price = original_price

            item.display_price = item.tax(price, currency=event.currency, include_bundled=True)

            if price != original_price:
                item.original_price = item.tax(original_price, currency=event.currency, include_bundled=True)
            else:
                item.original_price = (
                    item.tax(item.original_price, currency=event.currency, include_bundled=True,
                             base_price_is='net' if event.settings.display_net_prices else 'gross')  # backwards-compat
                    if item.original_price else None
                )

            display_add_to_cart = display_add_to_cart or item.order_max > 0
        else:
            for var in item.available_variations:
                if var.require_membership and var.require_membership_hidden:
                    if not memberships or not any([m.membership_type in var.require_membership_types.all() for m in memberships]):
                        var._remove = True
                        continue

                var.description = str(var.description)
                for recv, resp in item_description.send(sender=event, item=item, variation=var):
                    if resp:
                        var.description += ("<br/>" if var.description else "") + resp

                if voucher and (voucher.allow_ignore_quota or voucher.block_quota):
                    var.cached_availability = (
                        Quota.AVAILABILITY_OK, voucher.max_usages - voucher.redeemed
                    )
                else:
                    var.cached_availability = list(
                        var.check_quotas(subevent=subevent, _cache=quota_cache, include_bundled=True)
                    )

                var.order_max = min(
                    var.cached_availability[1]
                    if var.cached_availability[1] is not None else sys.maxsize,
                    max_per_order
                )

                original_price = var_price_override.get(var.pk, var.price)
                if voucher:
                    price = voucher.calculate_price(original_price)
                else:
                    price = original_price

                var.display_price = var.tax(price, currency=event.currency, include_bundled=True)

                if price != original_price:
                    var.original_price = var.tax(original_price, currency=event.currency, include_bundled=True)
                else:
                    var.original_price = (
                        var.tax(var.original_price or item.original_price, currency=event.currency,
                                include_bundled=True,
                                base_price_is='net' if event.settings.display_net_prices else 'gross')  # backwards-compat
                    ) if var.original_price or item.original_price else None

                display_add_to_cart = display_add_to_cart or var.order_max > 0

            item.original_price = (
                item.tax(item.original_price, currency=event.currency, include_bundled=True,
                         base_price_is='net' if event.settings.display_net_prices else 'gross')  # backwards-compat
                if item.original_price else None
            )

            item.available_variations = [
                v for v in item.available_variations if v._subevent_quotas and (
                    not voucher or not voucher.quota_id or v in restrict_vars
                ) and not getattr(v, '_remove', False)
            ]

            if not (ignore_hide_sold_out_for_item_ids and item.pk in ignore_hide_sold_out_for_item_ids) and event.settings.hide_sold_out:
                item.available_variations = [v for v in item.available_variations
                                             if v.cached_availability[0] >= Quota.AVAILABILITY_RESERVED]

            if voucher and voucher.variation_id:
                item.available_variations = [v for v in item.available_variations
                                             if v.pk == voucher.variation_id]

            if len(item.available_variations) > 0:
                item.min_price = min([v.display_price.net if event.settings.display_net_prices else
                                      v.display_price.gross for v in item.available_variations])
                item.max_price = max([v.display_price.net if event.settings.display_net_prices else
                                      v.display_price.gross for v in item.available_variations])
                item.best_variation_availability = max([v.cached_availability[0] for v in item.available_variations])

            item._remove = not bool(item.available_variations)

    if not quota_cache_existed and not voucher and not allow_addons and not base_qs_set and not filter_items and not filter_categories:
        event.cache.set(quota_cache_key, quota_cache, 5)
    items = [item for item in items
             if (len(item.available_variations) > 0 or not item.has_variations) and not item._remove]
    return items, display_add_to_cart
