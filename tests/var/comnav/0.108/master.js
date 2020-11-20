// Determines when a request is considered "timed out"
var timeOutMS = 5000; //ms
var profwin;
var globalXmlHttp;
var hillsBuild = false;
var variant = 1;

// Stores a queue of AJAX events to process
var ajaxList = new Array();

/**
 * stores the number of dots current being shown in the rescan button
 */
var scanDots = 0;

/**
 * current iteration of the bss info read from WiFi module.
 */
var currBss = 0;

/**
 * whether to destroy or build other networks table
 */
var otherNetworkExpanded = 1;


// Initiates a new AJAX command
//  url: the url to access
//  container: the document ID to fill, or a function to call with response XML (optional)
//  repeat: true to repeat this call indefinitely (optional)
//  data: an URL encoded string to be submitted as POST data (optional)
function newAJAXCommand(url, container, repeat, data)
{
  // Set up our object
  var newAjax = new Object();
  var theTimer = new Date();

  newAjax.url = url;
  newAjax.container = container;
  newAjax.repeat = repeat;
  newAjax.ajaxReq = null;

  if (data == null)
    data = "sess=" + getSession();
  else {
    data = "sess=" + getSession() + '&' + data;
  }

  // Create and send the request
  if (window.XMLHttpRequest) {
    newAjax.ajaxReq = new XMLHttpRequest();
    newAjax.ajaxReq.open((data == null) ? "GET" : "POST", newAjax.url, true);
    newAjax.ajaxReq.send(data);
    // If we're using IE6 style (maybe 5.5 compatible too)
  } else if (window.ActiveXObject) {
    newAjax.ajaxReq = new ActiveXObject("Microsoft.XMLHTTP");
    if (newAjax.ajaxReq) {
      newAjax.ajaxReq.open((data == null) ? "GET" : "POST", newAjax.url, true);
      newAjax.ajaxReq.send(data);
    }
  }

  newAjax.lastCalled = theTimer.getTime();
  // Store in our array
  ajaxList.push(newAjax);
}

// Loops over all pending AJAX events to determine if any action is required
function pollAJAX()
{
  var curAjax = new Object();
  var theTimer = new Date();
  var elapsed;

  // Read off the ajaxList objects one by one
  for (i = ajaxList.length; i > 0; i--) {
    curAjax = ajaxList.shift();
    if (!curAjax)
      continue;
    elapsed = theTimer.getTime() - curAjax.lastCalled;

    // If we succeeded
    if (curAjax.ajaxReq.readyState == 4 && curAjax.ajaxReq.status == 200 && curAjax.ajaxReq.responseText.substring(0, 9).toUpperCase() != "<!DOCTYPE") {
      // If it has a container, write the result
      if (typeof(curAjax.container) == 'function') {
        //curAjax.container(curAjax.ajaxReq.responseXML.documentElement);
        try {
          curAjax.container(curAjax.ajaxReq.responseText);
        } catch (err) {}
      } else if (typeof(curAjax.container) == 'string') {
        document.getElementById(curAjax.container).innerHTML = curAjax.ajaxReq.responseText;
      } // (otherwise do nothing for null values)

      curAjax.ajaxReq.abort();
      curAjax.ajaxReq = null;

      // If it's a repeatable request, then do so
      if (curAjax.repeat)
        newAJAXCommand(curAjax.url, curAjax.container, curAjax.repeat);
      continue;
    } else
    if (curAjax.ajaxReq.readyState == 4 && curAjax.ajaxReq.status == 200) {
      window.location.replace("/login.htm");
    }
    // If we've waited over 1 second, then we timed out
    if (elapsed > timeOutMS) {
      // Invoke the user function with null input
      if (typeof(curAjax.container) == 'function') {
        curAjax.container(null);

      } else {
        // Alert the user
        alert("Command failed.\nConnection to Panel was lost.");
        window.location.replace("/login.htm");

      }

      curAjax.ajaxReq.abort();
      curAjax.ajaxReq = null;

      // If it's a repeatable request, then do so
      if (curAjax.repeat)
        newAJAXCommand(curAjax.url, curAjax.container, curAjax.repeat);
      continue;
    }

    // Otherwise, just keep waiting
    ajaxList.push(curAjax);
  }

  // Call ourselves again in 10ms
  setTimeout("pollAJAX()", 300);
}

function callCalendar(what)
{
  try {
    cal.select(what, 'anchor1', 'dd/MM/yyyy');
  } catch (err) {
    cal.popupWindow.close();
    return;
  }
}

function getXMLValue(xmlData, field)
{
  result = "";

  if (xmlData != null) {
    tag = '<' + field + '>';
    var s = xmlData.indexOf(tag);
    var e = xmlData.indexOf('</' + field + '>');
    if (s >= 0 && e > s)
      result = xmlData.substring(s + tag.length, e);
  }

  return result;
}

function GetXmlHttpObject()
{
  var xmlHttp = null;

  try {
    // Firefox, Opera 8.0+, Safari
    xmlHttp = new XMLHttpRequest();
  } catch (e) {
    // Internet Explorer
    try {
      xmlHttp = new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e) {
      xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
    }
  }

  return xmlHttp;
}

function hideElement(whichElement)
{
  document.getElementById(whichElement).style.display = "none";
}

function viewElement(whichElement)
{
  document.getElementById(whichElement).style.display = "inline";
}

function textToNumber(text)
{
  var i;
  var mult = 1;
  var result = 0;

  for (i = 0; i < (text.length) / 2; i++) {
    result += parseInt(text.substring((2 * i), (2 * i) + 2), 16) * mult;
    mult *= 256;
  }
  return result;
}

function numberToText(text, digits)
{
  var number = parseInt(text);
  if (number < 0) {
    number += Math.pow(256, digits / 2);
  }
  var hexnumber = number.toString(16).toUpperCase();
  var result = "";
  if (hexnumber == "NAN")
    return result;
  while ((hexnumber.length) < digits)
    hexnumber = "0" + hexnumber;
  for (i = hexnumber.length; i > 0; i -= 2)
    result += hexnumber.substring(i - 2, i);
  return result;
}

function dateAndTimeToInt(value)
{
  fs = value.indexOf('/', 0);
  ss = value.indexOf('/', fs + 1);
  sp = value.indexOf(' ', 0);
  fc = value.indexOf(':', 0);
  sc = value.indexOf(':', fc + 1);
  year = parseInt(value.substring(ss + 1, sp), 10);
  if (year < 100)
    year += 2000;
  month = parseInt(value.substring(fs + 1, ss), 10);
  day = parseInt(value.substring(0, fs), 10);
  hr = parseInt(value.substring(sp + 1, fc), 10);
  if (sc == -1) {
    sec = 0;
    min = parseInt(value.substring(fc + 1, value.length), 10);
  } else {
    sec = parseInt(value.substring(sc + 1), 10);
    min = parseInt(value.substring(fc + 1, sc), 10);
  }
  if (sec < 0 || sec > 59)
    sec = 0;
  return Date.UTC(year, month - 1, day, hr, min, sec) / 1000;
}

function RFC3339dateAndTimeToInt(value)
{
  fs = value.indexOf('-', 0);
  ss = value.indexOf('-', fs + 1);
  sp = value.indexOf(' ', 0);
  fc = value.indexOf(':', 0);
  sc = value.indexOf(':', fc + 1);
  year = parseInt(value.substring(0, fs), 10);
  if (year < 100)
    year += 2000;
  month = parseInt(value.substring(fs + 1, ss), 10);
  day = parseInt(value.substring(ss + 1, sp), 10);
  hr = parseInt(value.substring(sp + 1, fc), 10);
  if (sc == -1) {
    sec = 0;
    min = parseInt(value.substring(fc + 1, value.length), 10);
  } else {
    sec = parseInt(value.substring(sc + 1), 10);
    min = parseInt(value.substring(fc + 1, sc), 10);
  }
  if (sec < 0 || sec > 59)
    sec = 0;

  return Date.UTC(year, month - 1, day, hr, min, sec) / 1000;
}

// convert "YYYY-MM-DD" to days since 1970-1-1
function RFC3339dateToInt(value)
{
  asa = value.split('-');
  year = parseInt(asa[0], 10);
  month = parseInt(asa[1], 10);
  day = parseInt(asa[2], 10);
  if (year < 100)
    year += 2000;
  result = Date.UTC(year, month - 1, day) / 86400000;

  return result;
}

function dateToInt(value)
{
  asa = value.split('/');
  year = parseInt(asa[2], 10);
  month = parseInt(asa[1], 10);
  day = parseInt(asa[0], 10);
  if (year < 100)
    year += 2000;
  result = Date.UTC(year, month - 1, day) / 86400000;

  return result;
}

function intToDate(k)
{
  myDate = new Date(k * 86400000);
  resp = myDate.getUTCDate() + '/' + (myDate.getUTCMonth() + 1) + '/' + myDate.getUTCFullYear();

  return resp;
}

function timeToInt(value)
{
  fc = value.indexOf(':', 0);
  hr = parseInt(value.substring(0, fc), 10);
  min = parseInt(value.substring(fc + 1), 10);

  return (hr * 60) + min;
}

function intToTime(dt)
{
  myDate = new Date(dt * 60000);
  resp = myDate.getUTCHours() + ':';
  if (myDate.getUTCMinutes() < 10)
    resp += '0';
  resp += myDate.getUTCMinutes();

  return resp;
}

function intToDateAndTime(dt)
{
  var myDate = new Date(dt * 1000);
  resp = myDate.getUTCDate() + '/' +
    (myDate.getUTCMonth() + 1) + '/' +
    myDate.getUTCFullYear() + ' ' +
    myDate.getUTCHours() + ':';
  if (myDate.getUTCMinutes() < 10)
    resp += '0';
  resp += myDate.getUTCMinutes() + ':';
  if (myDate.getUTCSeconds() < 10)
    resp += '0';
  resp += myDate.getUTCSeconds();

  return resp;
}

function pad(n)
{
  return n < 10 ? '0' + n : n
}

function justRFC3339Date(dt)
{
  var d = new Date(dt * 1000);
  resp = d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate());
  return resp;
}

function justDate(dt)
{
  dandt = intToDateAndTime(dt);
  return dandt.substring(0, dandt.indexOf(' ', 0));
}

function justTime(dt)
{
  dandt = intToDateAndTime(dt);
  return dandt.substring(dandt.indexOf(' ', 0) + 1);
}

function df(element)
{
  e = document.getElementById(element);
  e.select();
  e.focus();
}

function changeInputType(oldObject, oType)
{
  var newObject = document.createElement('input');

  newObject.type = oType;

  if (oldObject.value) newObject.value = oldObject.value;
  if (oldObject.readonly) newObject.readonly = oldObject.readonly;
  if (oldObject.disabled) newObject.disabled = oldObject.disabled;
  if (oldObject.onmouseover) newObject.onmouseover = oldObject.onmouseover;
  if (oldObject.onkeyup) newObject.onkeyup = oldObject.onkeyup;
  if (oldObject.onkeydown) newObject.onkeydown = oldObject.onkeydown;
  if (oldObject.onfocus) newObject.onfocus = oldObject.onfocus;
  if (oldObject.name) newObject.name = oldObject.name;
  if (oldObject.id) newObject.id = oldObject.id;
  if (oldObject.onclick) newObject.onclick = oldObject.onclick;
  if (oldObject.className) newObject.className = oldObject.className;
  oldObject.parentNode.replaceChild(newObject, oldObject);

  return newObject;
}

function getChannels(thisForm, formNo, formName)
{
  with(thisForm) {
    globalXmlHttp = GetXmlHttpObject();
    if (globalXmlHttp == null) {
      alert("Your browser does not support AJAX!");
      return;
    }
    var url = "/muser/chan.xml";
    var params = "sess=" + getSession();
    globalXmlHttp.open("POST", url, true);
    globalXmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    globalXmlHttp.onreadystatechange = function() {
      if (globalXmlHttp.readyState == 4) {
        if (globalXmlHttp.status == 200 && globalXmlHttp.responseText.substring(0, 9).toUpperCase() != "<!DOCTYPE") {

          var s = 0;
          var i = 0;
          var tbl1 = document.createElement('table');
          tbl1.id = ("chtab");

          for (; i < 16; i++) {
            cd = getXMLValue(globalXmlHttp.responseText, 'dest' + i);
            if (cd != "" && cd.length > 1 && cd.substring(0, 2) == formNo) {
              tbl1.insertRow(s);
              tbl1.rows[s].insertCell(0);
              tbl1.rows[s].insertCell(1);
              var lab = document.createTextNode(formName + (s + 1));
              tbl1.rows[s].insertCell(0).setAttribute('class', 'lab');
              tbl1.rows[s].cells[0].appendChild(lab);
              var ip = document.createElement('input');
              ip.setAttribute('type', 'text');
              ip.setAttribute('id', 'dest' + i);
              ip.setAttribute('class', 'txt');
              ip.value = cd.substring(2);
              tbl1.rows[s].cells[1].appendChild(ip);
              s++;
            }
          }
          document.getElementById('ct').appendChild(tbl1);


        } else
        if (globalXmlHttp.status == 403 || globalXmlHttp.status == 302 || globalXmlHttp.status == 404) {
          window.location.replace("/login.htm");
        }
        globalXmlHttp = null;
      }
    }
    globalXmlHttp.send(params);
  }
}

function putChannels(thisForm, params)
{
  with(thisForm) {
    globalXmlHttp = GetXmlHttpObject();
    if (globalXmlHttp == null) {
      alert("Your browser does not support AJAX!");
      return;
    }
    var url = "/muser/chan.cgi";
    var i = 0;
    for (; i < 16; i++) {
      if (document.getElementById('dest' + i) != null)
        params += "&dest" + i + "=" + document.getElementById('dest' + i).value;
    }
    globalXmlHttp.open("POST", url, true);
    globalXmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    globalXmlHttp.onreadystatechange = function() {
      if (globalXmlHttp.readyState == 4 && globalXmlHttp.status == 200) {
        if (globalXmlHttp.responseText.substring(0, 9).toUpperCase() == "<!DOCTYPE") {
          window.location.replace("/login.htm");
        } else {
          alert(globalXmlHttp.responseText);
          document.getElementById('users').focus();
        }
        globalXmlHttp = null;
      } else
      if (globalXmlHttp.status == 403) {
        window.location.replace("/login.htm");
        globalXmlHttp = null;
      }

    }
    globalXmlHttp.send(params);
  }
}

function testCGIResponse(response)
{
  try {
    if (response.substring(0, 9).toUpperCase() == "<!DOCTYPE") {
      window.location.replace("/login.htm");
    } else
    if (response != null && response != "")
      alert(response);

  } catch (err) {
    alert("" + err);
  }
}


function toggle_vis(id)
{
  var e = document.getElementById(id);
  e.style.display = ((e.style.display != 'block') ? 'block' : 'none');
}

function buildBanner(name)
{
  /* Build this html
  <div class="ban">
    <button class="mnu-btn" onclick="toggle_vis('mnu');">Menu</button>
    <p>xGen</p>
  </div>
  */
  var d = document.createElement('div');

  d.id = 'ban';
  d.setAttribute('class', 'ban');
  d.innerHTML =
    '<button type="button" class="mnu-btn" onclick="toggle_vis(\'mnu\');">Menu</button><p></p>';
  d.getElementsByTagName("p")[0].innerHTML = name;
  document.getElementById('w').appendChild(d);
}

function buildMenu(active, ma0, ma1, ma2, ma3, ma4)
{
  /* Build this html and append as child of <div id="w"></div>
  <div id="mnu">
      <form method="post" id="newpage"  action="/index.htm" name="newpage1">
      <input type="hidden" id="sess1" name="sess" value="~sess~"/>
      </form>
      <ul class="nav">
      <li>...</li>
      ...
      <li>...</li>
      </ul>
  </div>
  */
  var d = document.createElement("div");
  d.id = 'mnu';
  var mstring =
    '<form method="post" id="newpage"  action="/logout.cgi" name="newpage1"> \
    <input type="hidden" id="sess1" name="sess"/> \
    </form> \
    <ul class="nav"> \
    <li><a onclick="document.getElementById(\'newpage\').submit(); ">'+menuNames[0]+'</a></li> \
    <li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\', \'/user/area.htm\'); document.getElementById(\'newpage\').submit();" >'+menuNames[1]+'</a></li> \
    <li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/user/zones.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[2]+'</a></li>\
    <li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/user/outputs.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[3]+'</a></li>';

  var mcnt = 3;

  if (ma2 == 1) {
    mcnt++;
    if (active == 4)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/user/history.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[4]+'</a></li>';
  }
  if (ma1 == 1) {
    mcnt++;
    if (active == 5)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/configpins.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[5]+'</a></li>';
    mcnt++;
    if (active == 6)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/config6.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[6]+'</a></li>';
    // Leave SMS reporting out from US & EU builds
    if (variant != 1 && variant != 2) {
      mcnt++;
      if (active == 7)
        active = mcnt;
      mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/config3.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[7]+'</a></li>';
    }
    // Leave voice reporting out from US build
    if (variant != 1) {
      mcnt++;
      if (active == 8)
        active = mcnt;
      mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/config2.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[8]+'</a></li>';
    }
  }
  if (ma0 == 1) {
    mcnt++;
    if (active == 9)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config1.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[9]+'</a></li>';
    mcnt++;
    if (active == 10)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config5.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[10]+'</a></li>';
    mcnt++;
    if (active == 11)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config7.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[11]+'</a></li>';
    mcnt++;
    if (active == 12)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config8.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[12]+'</a></li>';

  }
  if (ma1 == 1) {
    mcnt++;
    if (active == 13)
      active = mcnt;
    mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/textnames.htm\');document.getElementById(\'newpage\').submit(); ">'+menuNames[13]+'</a></li>';
  }
  mstring += '</ul>';
  d.innerHTML = mstring;
  d.getElementsByTagName('input')[0].setAttribute('value', getSession());
  d.getElementsByTagName('li')[active].className = 'active';
  document.getElementById('w').appendChild(d);
}

// function called by iPhone to check the number of menus and their names
// authorisation is checked separately by getMenu() which must be in the html as it contains variables
function getMenuNames()
{
  return appMenuNames;
}

// function called by iPhone to check the icons for menus
// function called by iPhone to check the icons for menus
function getMenuIcons()
{
  return '["lock","pir","lock","clock","users","email","sms","phone","spanner","network","spanner","spanner","spanner"]';
}

// function called by iPhone to goto a new page
// the param n is the index into the menunames array above
// ie is not in the same order as ~ma(x)~
// menus:
// n  URL
// 0  /user/area.htm        ~ma(3)~
// 1  /user/zones.htm       ~ma(4)~
// 2  /user/outputs.htm       ~ma(4)~
// 3  /user/history.htm     ~ma(2)~
// 4  /muser/configpins.htm ~ma(1)~
// 5  /muser/config6        ~ma(1)~     //Email
// 6  /muser/config3        ~ma(1)~     //sms
// 7  /muser/config2        ~ma(1)~     //Voice
// 8  /protect/config1.htm   ~ma(0)~    //Features
// 9  /protect/config5      ~ma(0)~     //Network
//10   /protect/config7     ~ma(0)~     //Outputs
//11 /protect/Config8       ~ma(0)~     //IP Reporting
//12 /muser/textnames       ~ma(0)~     //Name Editor
function submitMenu(n)
{
  if (n == 0)
    document.getElementById('newpage').setAttribute('action', '/user/area.htm');
  else if (n == 1)
    document.getElementById('newpage').setAttribute('action', '/user/zones.htm');
  else if (n == 2)
    document.getElementById('newpage').setAttribute('action', '/user/outputs.htm');
  else if (n == 3)
    document.getElementById('newpage').setAttribute('action', '/user/history.htm');
  else if (n == 4)
    document.getElementById('newpage').setAttribute('action', '/muser/configpins.htm');
  else if (n == 5)
    document.getElementById('newpage').setAttribute('action', '/muser/config6.htm');
  else if (n == 6)
    document.getElementById('newpage').setAttribute('action', '/muser/config3.htm');
  else if (n == 7)
    document.getElementById('newpage').setAttribute('action', '/muser/config2.htm');
  else if (n == 8)
    document.getElementById('newpage').setAttribute('action', '/protect/config1.htm');
  else if (n == 9)
    document.getElementById('newpage').setAttribute('action', '/protect/config5.htm');
  else if (n == 10)
    document.getElementById('newpage').setAttribute('action', '/protect/config7.htm');
  else if (n == 11)
    document.getElementById('newpage').setAttribute('action', '/protect/config8.htm');
  else if (n == 12)
    document.getElementById('newpage').setAttribute('action', '/muser/textnames.htm');
  else if (n == 999)
    document.getElementById('newpage').setAttribute('action', '/logout.cgi');
  else
    return;

  document.getElementById('newpage').submit();

  return;
}

// function used by iPhone app to setup web page to run in an app
function setAppMode()
{
  var e = document.getElementById('ban');
  e.style.display = 'none'; // hide the banner
  var e = document.getElementById('mnu');
  e.style.display = 'none'; // hide the side menu (shows on ipad)
}

//checks a name string for illegal characters
function checkNameEntry(nid, length)
{
  var newData = document.getElementById(nid).value

  if (newData.match(nameRegex) != null) {
    alert("Data must only contain the following characters" + nameAllowedChars);
    newData = removeBadCharacters(newData, nameRegex);
    document.getElementById(nid).value = newData;
    return true;
  }

  if (newData.length > length) {
    alert("Data limited to " + length + " characters!");
    document.getElementById(nid).value = newData.substring(0, length);
  }

  return false;
}

function removeBadCharacters(thestring, theregexp)
{
  while (thestring.match(theregexp) != null) {
    var badone = thestring.indexOf(thestring.match(theregexp));
    thestring = thestring.substring(0, badone) + thestring.substring(badone + 1);
  }

  return thestring;
}

function fillNames(id, namearray)
{
  var optionarray = document.getElementById(id);

  for (var i = 0; i < optionarray.options.length; i++)
    optionarray.options[i].innerHTML = namearray[i];
}

function convertNames(namearray)
{
  var e;

  for (var i = 0; i < namearray.length; i++) {
    try {
      namearray[i] = decodeURIComponent(decode_utf8(namearray[i]));
    } catch (err) {
      alert(namearray[i]);
    }
  }
}

function encode_utf8(s)
{
  //return unescape( encodeURIComponent( s ) );
  //need to use the language encoder
  return s;
}

function decode_utf8(s)
{
  //return escape( decodeURIComponent( s ) );
  //need to use the language decoder
  return s;
}

//kick off the AJAX Updater
setTimeout("pollAJAX()", 300);
