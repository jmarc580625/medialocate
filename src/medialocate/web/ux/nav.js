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


Tour Eiffel = 48.8583573655146, 2.2943976077605215
Arc de Triomphe = 48.873772665953275, 2.295011556033665
place de la Bastille = 48.853158362623056, 2.369119922346588
Moulin rouge = 48.88414406517008, 2.3322587941431605
Grande Arche de la Défense = 48.892553697408204, 2.2358913961612084
Champs de Mars = 48.85610796211571, 2.297870751726531
Grand Palais = 48.86648039669161, 2.3123502768613102
Cathédrale Notre-Dame de Paris = 48.853005936177475, 2.349951262116572
Hotel de Ville = 48.85646285878103, 2.352447257426543
Hôtel des Invalides = 48.855054393361314, 2.3124988422017156
Jardin des Tuileries = 48.862908746047175, 2.329278293966599
Musée du Louvre = 48.86061118408578, 2.3376336827411857
Panthéon = 48.846213173890476, 2.3461314133134463
Place de la Concorde = 48.86561891134583, 2.321248710895361
Basilique du Sacré-Cœur de Montmartre = 48.886678049479436, 2.342994950973606
Sainte-Chapelle = 48.48.85542259927059, 2.344944792635914
*/
