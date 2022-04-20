var map;
var marker;

function initialize() {
    var myLatlng = new google.maps.LatLng(25.2048, 55.2708);

    var myOptions = {
        zoom: 8,
        center: myLatlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

    marker = new google.maps.Marker({
        draggable: true,
        position: myLatlng,
        map: map,
        title: "Your location"
    });

    google.maps.event.addListener(marker, 'dragend', function(event) {


        document.getElementById("lat").value = event.latLng.lat();
        document.getElementById("long").value = event.latLng.lng();
    });

    google.maps.event.addListener(map, 'click', function(event) {


        document.getElementById("lat").value = event.latLng.lat();
        document.getElementById("long").value = event.latLng.lng();
        marker.setPosition(event.latLng);
    });
}
google.maps.event.addDomListener(window, "load", initialize());