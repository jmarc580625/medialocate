// Converts measure from degree to radian
function degreeToRadian(degrees) {
  return degrees * Math.PI / 180;
};      

// Converts measure from radian to degree
function radianToDegree(radians) {
  return radians * 180 / Math.PI;
}

// get bearing angle in degree between two GPS positions
function getBearing(origin, destination){
  startLat = degreeToRadian(origin.latitude);
  startLng = degreeToRadian(origin.longitude);
  destLat = degreeToRadian(destination.latitude);
  destLng = degreeToRadian(destination.longitude);

  y = Math.sin(destLng - startLng) * Math.cos(destLat);
  x = Math.cos(startLat) * Math.sin(destLat) -
        Math.sin(startLat) * Math.cos(destLat) * Math.cos(destLng - startLng);

  bearing = radianToDegree(Math.atan2(y, x));
  return (bearing + 360) % 360;
}

// get distance in kilometer between two GPS positions
function getDistance(origin, destination){
  var earthRadiusKm = 6371;

  var dLat = degreeToRadian(destination.latitude-origin.latitude);
  var dLon = degreeToRadian(destination.longitude-origin.longitude);

  var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
          Math.sin(dLon/2) * Math.sin(dLon/2) * Math.cos(degreeToRadian(origin.latitude)) * Math.cos(degreeToRadian(destination.latitude)); 
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
  return earthRadiusKm * c;
}

/* test nav functions
gpsGreenWichEquator = {latitude:0,          longitude:0};
gpsGreenWichCity    = {latitude:51.5,       longitude:0};
gpsAlexandria       = {latitude:38.8,       longitude:-77.1}
gpsStLouis          = {latitude:38.627089,  longitude:-90.200203};
gpsKansasCity       = {latitude:39.099912,  longitude:-94.581213};
gpsNothPole         = {latitude:90,         longitude:0};
gpsSouthPole        = {latitude:-90,        longitude:0};
console.log("checks distance is nul: "+getDistance(gpsGreenWichEquator,gpsGreenWichEquator));
console.log("checks distance is nul: "+getDistance(gpsGreenWichCity,gpsGreenWichCity));
console.log("checks distance is 5918.185064088764: "+getDistance(gpsGreenWichCity, gpsAlexandria)); 
console.log("distance from Kansas City to St Louis (382,901 kilometers) : "+getDistance(gpsKansasCity, gpsStLouis));
console.log("bearing angle from Kansas City to St Louis (96.513°) : "+getBearing(gpsKansasCity, gpsStLouis));
console.log("bearing angle from Greenwich equator to noth pole (0°) : "+getBearing(gpsGreenWichEquator, gpsNothPole));
console.log("bearing angle from Greenwich equator to south pole (180°) : "+getBearing(gpsGreenWichEquator, gpsSouthPole));
*/
