// the http request function
function httpGetAsync(theUrl, callback)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}




var checbox_val  = ''
// a Function that make sure only one product is selected
function check()
{

        input = this
        var checkboxes = document.getElementsByClassName("radioCheck");
        
        for(var i = 0; i < checkboxes.length; i++)
        {
                //uncheck all
                if(checkboxes[i].checked == true)
                {
                        checkboxes[i].checked = false;
                }
        }
        
        //set checked of clicked object
        if(input.checked == true)
        {
                input.checked = false;
        }
        else
        {
                input.checked = true;
        }	
        checbox_val = input.getAttribute("name")
}

var checkboxes = document.getElementsByClassName("radioCheck");

for (var h = 0;h<checkboxes.length;h++){
        checkboxes[h].addEventListener("click", check);
}

var subevent = document.getElementById('subevent-list');
var button = document.getElementsByClassName("subevent-toggle btn btn-default btn-block")[0];
console.log(button)






// the canvas thing
var elem = document.getElementById('myCanvas');
elements = [];
elem.addEventListener('click', function(event) {
        var elemLeft = elem.offsetLeft
        var elemTop = elem.offsetTop 
        let scrollleft = document.getElementById("container_floay").scrollLeft 
        console.log('scroll == >',scrollleft)
        var x = event.pageX - elemLeft + scrollleft,
            y = event.pageY - elemTop;
        console.log(       )
        // Collision detection between clicked offset and element.
        elements.forEach(function(element) {
            if (y > element.top && y < element.top + element.height 
                && x > element.left && x < element.left + element.width) {
                       window.location.href = location.toString().replace(location.search, "")
                         + '?category_seat='+ element.category + '&seat_guid='+element.seat_guid
            }
        });
    
    }, false);
// set style

document.getElementById("container_floay").style.max_width = "90vw"
document.getElementById("container_floay").style.overflow = "auto"



//  
var button_url = document.getElementById("url_data")
var txt = button_url.value



const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
      });
if  (params.seat_guid == undefined || typeof params.seat_guid == 'undefined'){

httpGetAsync(window.location.protocol+'//'+window.location.host +txt,res => {
        data_first = JSON.parse(res)
        console.log(data_first)
        unv_seats = data_first.seats
        data = data_first.seating_plan
        console.log(unv_seats)
        var c = document.getElementById("myCanvas");
        c.height = data.layout.size.height
        c.width = data.layout.size.width

        //c.width = 300
        const ctx = c.getContext('2d')
      
        layout = data.layout
        for (var i =0 ; i<layout.zones.length; i++){
                categories = layout.categories
                color_dict = {}
                for (var c =0 ;c<categories.length; c ++){
                        color_dict[categories[c].name] = categories[c].color
                }

                zone = layout.zones[i]
                rows = zone.rows
                for (var j = 0 ; j<zone.areas.length; j++){

                        // draw the areas
                        area = zone.areas[j]
                        
                        ctx.fillStyle = area.color
                        ctx.lineWidth = 2;
                        ctx.strokeStyle  = area.border_color
                        if (area.shape == 'rectangle'){
                                ctx.beginPath();
                                ctx.rect(area.position.x, area.position.y, area.rectangle.width, area.rectangle.height)
                                ctx.fill()
                                ctx.stroke()                                
                        }else if (area.shape == 'circle'){
                                ctx.beginPath();
                                ctx.arc(area.position.x, area.position.y, area.circle.radius , 0, 2 * Math.PI)
                                ctx.fill()
                                ctx.stroke()     
                        }else if (area.shape =='ellipse'){
                                ctx.beginPath();
                                ctx.ellipse(area.position.x, area.position.y, area.ellipse.radius.x ,area.ellipse.radius.y, area.rotation* (Math.PI / 180.0), 0, 2 * Math.PI,true)
                                ctx.fill()
                                ctx.stroke()       
                        }else if (area.shape =='text'){
                                ctx.font = area.text.size.toString() + 'px Arial';
                                ctx.fillStyle = area.text.color;
                                ctx.textAlign = 'center';
                                ctx.fillText(area.text.text, area.position.x + area.text.position.x, area.position.y+area.text.position.y);
                        }else if (area.shape == 'polygon'){
                                area_x = area.position.x
                                area_y = area.position.y
                                points = area.polygon.points
                                ctx.beginPath()
                                ctx.moveTo(points[0].x+area_x,points[0].y+area_y)
                                for (var p = 1; p< points.length ; p++){
                                        ctx.lineTo(points[p].x+area_x,points[p].y+area_y);
                                }
                                ctx.closePath()
                                ctx.fill()
                                ctx.stroke()
                        }
                }
                for (var k=0;k<rows.length;k++){
                                // draw the rows
                                pre_pos_x = rows[k].position.x
                                pre_pos_y = rows[k].position.y
                                seats = rows[k].seats
                                ctx.font = '11pt Calibri';
                                ctx.fillStyle = 'black';
                                ctx.textAlign = 'center';
                                ctx.fillText(rows[k].row_number, pre_pos_x-20, pre_pos_y+3);
                                for (var l=0;l<seats.length;l++){
                                        // draw the seats
                                        seat_x = seats[l].position.x + pre_pos_x
                                        seat_y = seats[l].position.y + pre_pos_y
                                        radius = seats[l].radius
                                        number = seats[l].seat_number
                                        seat_guid = seats[l].seat_guid
                                        id = seats[l].uuid
                                        if ( typeof  seats[l].radius == 'undefined') {
                                                radius = 10
                                        }
                                        // draw the circle
                                        ctx.beginPath();
                                        ctx.fillStyle = "White"
                                        if (color_dict[seats[l].category] != ""){
                                                color_cat = color_dict[seats[l].category] ;
                                        }
                                        ctx.lineWidth = 1;
                                        ctx.arc(seat_x, seat_y, radius, 0, 2 * Math.PI);
                                        ctx.stroke()
                                        if  (!(unv_seats.includes(seat_guid))) {
                                        ctx.fillStyle = color_cat
                                        
                                        ctx.fill();
                                        
                                        // write the seat number

                                        ctx.font = '9pt Calibri';
                                        ctx.fillStyle = 'black';
                                        ctx.textAlign = 'center';
                                        ctx.fillText(number, seat_x, seat_y+3);

                                        elements.push({
                                                category : seats[l].category,
                                                width: radius*2,
                                                height: radius*2,
                                                id : id,
                                                seat_guid : seat_guid,
                                                top: seat_y-radius,
                                                left: seat_x-radius
                                            });

                                        }else {
                                                console.log(unv_seats.includes(seat_guid))
                                        }
                                }
                                ctx.font = '11pt Calibri';
                                ctx.fillStyle = 'black';
                                ctx.textAlign = 'center';
                                ctx.fillText(rows[k].row_number, seat_x+20, pre_pos_y+3);

                                
                        }
                
        }

        elements.forEach(function(element) {
                if (element.seat_guid=="Groundfloor-a-1") {
                            console.log('element =>',element)
        
                }
               // console.log(element.seat_guid)
            });
})

}


//
var button_url_assign = document.getElementById("url_data_assign")
var text_assign = button_url_assign.value

function processForm(e) {
        if (e.preventDefault) e.preventDefault();

        httpGetAsync(window.location.protocol+'//'+window.location.host +text_assign+'?seat_guid='+params.seat_guid+'&item='+checbox_val,res => {
                console.log('the response ===>',res)
});

        /* do what you want with the form */
    
        // You must return false to prevent the default form behavior
        return false;
    }
    
    var form = document.querySelector('form.has-seating');
    console.log('form',form)
    if (form.attachEvent) {
        form.attachEvent("submit", processForm);
    } else {
        form.addEventListener("submit", processForm);
    }

var button_add = document.getElementById('btn-add-to-cart')
console.log(button_add)
if  (params.seat_guid == undefined || typeof params.seat_guid == 'undefined'){
        console.log(button_add)
        button_add.style.visibility = 'hidden';
}