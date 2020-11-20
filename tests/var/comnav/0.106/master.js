// Determines when a request is considered "timed out"
var timeOutMS = 5000; //ms
var profwin;
var globalXmlHttp;


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
//	url: the url to access
//	container: the document ID to fill, or a function to call with response XML (optional)
//	repeat: true to repeat this call indefinitely (optional)
//	data: an URL encoded string to be submitted as POST data (optional)
function newAJAXCommand(url, container, repeat, data)
{
	// Set up our object
	var newAjax = new Object();
	var theTimer = new Date();
	newAjax.url = url;
	newAjax.container = container;
	newAjax.repeat = repeat;
	newAjax.ajaxReq = null;

	if(data == null)
        data = "sess="+getSession(); 
    else
        {
           data = "sess="+getSession() + '&' + data;
 	    }
	// Create and send the request
	if(window.XMLHttpRequest) {
        newAjax.ajaxReq = new XMLHttpRequest();
        newAjax.ajaxReq.open((data==null)?"GET":"POST", newAjax.url, true);
        newAjax.ajaxReq.send(data);
    // If we're using IE6 style (maybe 5.5 compatible too)
    } else if(window.ActiveXObject) {
        newAjax.ajaxReq = new ActiveXObject("Microsoft.XMLHTTP");
        if(newAjax.ajaxReq) {
            newAjax.ajaxReq.open((data==null)?"GET":"POST", newAjax.url, true);
            newAjax.ajaxReq.send(data);
        }
    }
    
    newAjax.lastCalled = theTimer.getTime();
     // Store in our array
    ajaxList.push(newAjax);
}

// Loops over all pending AJAX events to determine if any action is required
function pollAJAX() {	
	var curAjax = new Object();
	var theTimer = new Date();
	var elapsed;
	
	// Read off the ajaxList objects one by one
	for(i = ajaxList.length; i > 0; i--)
	{
		curAjax = ajaxList.shift();
		if(!curAjax)
			continue;
		elapsed = theTimer.getTime() - curAjax.lastCalled;
				
		// If we succeeded
		if(curAjax.ajaxReq.readyState == 4 && curAjax.ajaxReq.status == 200 && curAjax.ajaxReq.responseText.substring(0,9).toUpperCase() != "<!DOCTYPE" ) {
			// If it has a container, write the result
			if(typeof(curAjax.container) == 'function'){
				//curAjax.container(curAjax.ajaxReq.responseXML.documentElement);
				try{
				curAjax.container(curAjax.ajaxReq.responseText);
				}catch(err){}
			} else if(typeof(curAjax.container) == 'string') {
				document.getElementById(curAjax.container).innerHTML = curAjax.ajaxReq.responseText;
			} // (otherwise do nothing for null values)
			
	    	curAjax.ajaxReq.abort();
	    	curAjax.ajaxReq = null;

			// If it's a repeatable request, then do so
			if(curAjax.repeat)
				newAJAXCommand(curAjax.url, curAjax.container, curAjax.repeat);
			continue;
		}
		else
      		if(curAjax.ajaxReq.readyState == 4 && curAjax.ajaxReq.status == 200)
      		{
               window.location.replace("/login.htm");
		    }
		// If we've waited over 1 second, then we timed out
		if(elapsed > timeOutMS) {
			// Invoke the user function with null input
			if(typeof(curAjax.container) == 'function'){
				curAjax.container(null);
				
			} else {
				// Alert the user
				alert("Command failed.\nConnection to Panel was lost.");
                window.location.replace("/login.htm");

			}

	    	curAjax.ajaxReq.abort();
	    	curAjax.ajaxReq = null;
			
			// If it's a repeatable request, then do so
			if(curAjax.repeat)
				newAJAXCommand(curAjax.url, curAjax.container, curAjax.repeat);
			continue;
		}
		
		// Otherwise, just keep waiting
		ajaxList.push(curAjax);
	}
	
	// Call ourselves again in 10ms
	setTimeout("pollAJAX()",300);
	
}

function callCalendar(what)
{
    try{
    cal.select(what,'anchor1','dd/MM/yyyy');
    }catch(err){cal.popupWindow.close();return;}
}

function getXMLValue(xmlData, field)
{   result = "";

    if(xmlData != null)
    {
        tag = '<'+field +'>';
        var s = xmlData.indexOf(tag);
        var e = xmlData.indexOf('</'+field +'>');
        if(s >= 0 && e > s)
         result = xmlData.substring(s+tag.length,e);
    }
    return result;
}

function GetXmlHttpObject()
{
var xmlHttp=null;
try
  {
  // Firefox, Opera 8.0+, Safari
  xmlHttp=new XMLHttpRequest();
  }
catch (e)
  {
  // Internet Explorer
  try
    {
    xmlHttp=new ActiveXObject("Msxml2.XMLHTTP");
    }
  catch (e)
    {
    xmlHttp=new ActiveXObject("Microsoft.XMLHTTP");
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
 
    for(i = 0; i < (text.length)/2;i++)
    {
        result += parseInt(text.substring((2*i),(2*i)+2),16)*mult; 
        mult *= 256;   
    }
    return result;
}

function numberToText(text, digits)
{
    var number = parseInt(text);
    if(number < 0)
    {
       number+=Math.pow(256,digits/2);
    }
    var hexnumber = number.toString(16).toUpperCase();
    var result = "";
    if(hexnumber == "NAN")
        return result;    
    while((hexnumber.length) < digits)
        hexnumber = "0" + hexnumber;
    for(i = hexnumber.length; i > 0  ; i-=2)
        result += hexnumber.substring(i-2,i);
    return result;
}

function dateAndTimeToInt(value)
{ 
   fs=value.indexOf('/',0); 
   ss=value.indexOf('/',fs+1);
   sp=value.indexOf(' ',0); 
   fc=value.indexOf(':',0); 
   sc=value.indexOf(':',fc+1);
   year=parseInt(value.substring(ss+1,sp),10);
   if(year<100)
     year+=2000;
   month=parseInt(value.substring(fs+1,ss),10);
   day=parseInt(value.substring(0,fs),10);
   hr=parseInt(value.substring(sp+1,fc),10);
   if(sc == -1)
   {
        sec = 0;
        min = parseInt(value.substring(fc+1,value.length),10);
   }     
   else 
        {
            sec=parseInt(value.substring(sc+1),10);
            min = parseInt(value.substring(fc+1,sc),10);
        }
   if(sec < 0 || sec > 59)
     sec = 0;
    return Date.UTC(year,month-1,day,hr,min,sec)/1000; 
}
function RFC3339dateAndTimeToInt(value)
{ 
   fs=value.indexOf('-',0); 
   ss=value.indexOf('-',fs+1);
   sp=value.indexOf(' ',0); 
   fc=value.indexOf(':',0); 
   sc=value.indexOf(':',fc+1);
   year=parseInt(value.substring(0,fs),10);
   if(year<100)
     year+=2000;
   month=parseInt(value.substring(fs+1,ss),10);
   day=parseInt(value.substring(ss+1,sp),10);
   hr=parseInt(value.substring(sp+1,fc),10);
   if(sc == -1)
   {
        sec = 0;
        min = parseInt(value.substring(fc+1,value.length),10);
   }     
   else 
        {
            sec=parseInt(value.substring(sc+1),10);
            min = parseInt(value.substring(fc+1,sc),10);
        }
   if(sec < 0 || sec > 59)
     sec = 0;
    return Date.UTC(year,month-1,day,hr,min,sec)/1000; 
}
// convert "YYYY-MM-DD" to days since 1970-1-1
function RFC3339dateToInt(value)
{
    asa = value.split('-');
    year = parseInt(asa[0],10);
    month=parseInt(asa[1],10);
    day=parseInt(asa[2],10);
    if(year<100)
     year+=2000;
   result = Date.UTC(year,month-1,day)/86400000;
  return result;   
}
function dateToInt(value)
{
    asa = value.split('/');
    year = parseInt(asa[2],10);
    month=parseInt(asa[1],10);
    day=parseInt(asa[0],10);
    if(year<100)
     year+=2000;
   result = Date.UTC(year,month-1,day)/86400000;
  return result;   
}
function intToDate(k)
{
	myDate = new Date(k*86400000);
	resp = myDate.getUTCDate()+ '/' + (myDate.getUTCMonth() +1)+ '/' + myDate.getUTCFullYear();  
	return resp;        
}

function timeToInt(value)
{
  fc=value.indexOf(':',0); 
  hr=parseInt(value.substring(0,fc),10);
  min=parseInt(value.substring(fc+1),10);
  return (hr*60)+min;
}

function intToTime(dt)
{
	myDate = new Date(dt*60000);
	resp = myDate.getUTCHours() + ':';
	if(myDate.getUTCMinutes() < 10)
	    resp += '0';
	resp += myDate.getUTCMinutes();   
    return resp;
}

function intToDateAndTime(dt)
{
	var myDate = new Date(dt*1000);
	resp = myDate.getUTCDate()+'/'+ 
	       (myDate.getUTCMonth()+1)+'/'+ 
	       myDate.getUTCFullYear()+' '+
		   myDate.getUTCHours()+':';
	if(myDate.getUTCMinutes() < 10)
	    resp += '0';
    resp += myDate.getUTCMinutes() + ':';
    if(myDate.getUTCSeconds() < 10)
        resp += '0';
    resp += myDate.getUTCSeconds();
    
    return resp;
}
function pad(n){return n<10 ? '0'+n : n}
function justRFC3339Date(dt)
{
  var d = new Date(dt*1000);
  resp = d.getUTCFullYear() + '-' + pad(d.getUTCMonth()+1) + '-' + pad(d.getUTCDate()); 
  return resp;  
}
function justDate(dt)
{
    dandt = intToDateAndTime(dt);
    return dandt.substring(0,dandt.indexOf(' ',0));
}
function justTime(dt)
{
    dandt = intToDateAndTime(dt);
    return dandt.substring(dandt.indexOf(' ',0)+1);
}
function df(element)
{
    e = document.getElementById(element);
    e.select();
    e.focus();
}
function changeInputType(oldObject, oType) {
var newObject = document.createElement('input');

  newObject.type = oType;
  
  if(oldObject.value) newObject.value = oldObject.value;
  if(oldObject.readonly) newObject.readonly = oldObject.readonly;
  if(oldObject.disabled) newObject.disabled = oldObject.disabled;
  if(oldObject.onmouseover) newObject.onmouseover = oldObject.onmouseover;
  if(oldObject.onkeyup) newObject.onkeyup = oldObject.onkeyup;
  if(oldObject.onkeydown) newObject.onkeydown = oldObject.onkeydown;
  if(oldObject.onfocus) newObject.onfocus = oldObject.onfocus;
  if(oldObject.name) newObject.name = oldObject.name;
  if(oldObject.id) newObject.id = oldObject.id;
  if(oldObject.onclick) newObject.onclick = oldObject.onclick;
  if(oldObject.className) newObject.className = oldObject.className;
  oldObject.parentNode.replaceChild(newObject,oldObject);
  return newObject;
}

function getChannels(thisForm, formNo,formName)
{ 
    with(thisForm)
    {
        globalXmlHttp=GetXmlHttpObject();
        if (globalXmlHttp==null)
        {
            alert ("Your browser does not support AJAX!");
            return;
        } 
        var url="/muser/chan.xml";
        var params="sess="+getSession(); 
        globalXmlHttp.open("POST",url,true);
        globalXmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
 
            globalXmlHttp.onreadystatechange = function() 
            {
                if(globalXmlHttp.readyState == 4) 
                {
                    if(globalXmlHttp.status == 200 && globalXmlHttp.responseText.substring(0,9).toUpperCase() != "<!DOCTYPE" )
                    {   
                    
                        var s = 0;
                        var i = 0;
                        var tbl1 =  document.createElement('table');
                        tbl1.id = ("chtab");
                        
                        for(;i < 16;i++)
                        {
                            cd=getXMLValue(globalXmlHttp.responseText, 'dest'+i);
                            if(cd != "" && cd.length >1 && cd.substring(0,2) == formNo)
                            {
                                tbl1.insertRow(s);
                                tbl1.rows[s].insertCell(0);
                                tbl1.rows[s].insertCell(1);
                                var lab = document.createTextNode(formName + (s + 1));
                                tbl1.rows[s].insertCell(0).setAttribute('class', 'lab');
                                tbl1.rows[s].cells[0].appendChild(lab);
                                var ip = document.createElement('input');
                                ip.setAttribute('type', 'text');
                                ip.setAttribute('id', 'dest'+i);
                                ip.setAttribute('class', 'txt');
                                ip.value = cd.substring(2);
                                tbl1.rows[s].cells[1].appendChild(ip);
                                s++;
                            } 
                        }
                        document.getElementById('ct').appendChild(tbl1);                 
 

                    }
                    else
                        if(globalXmlHttp.status == 403 || globalXmlHttp.status == 302 || globalXmlHttp.status == 404)
                        {
                            window.location.replace("/login.htm");
                        }       
                    globalXmlHttp = null;  
                }
            }  
        globalXmlHttp.send(params);
    }
}

function putChannels(thisForm,params)
{ 
    with(thisForm)
    {
        globalXmlHttp=GetXmlHttpObject();
        if (globalXmlHttp==null)
        {
            alert ("Your browser does not support AJAX!");
            return;
        } 
        var url="/muser/chan.cgi";
        var i = 0;
        for(;i<16;i++)
        {
            if(document.getElementById('dest'+i) != null)
                params += "&dest"+i+"="+document.getElementById('dest'+i).value;
        }
        globalXmlHttp.open("POST",url,true);
        globalXmlHttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        globalXmlHttp.onreadystatechange = function() 
        {
            if(globalXmlHttp.readyState == 4 && globalXmlHttp.status == 200) 
            {
                if(globalXmlHttp.responseText.substring(0,9).toUpperCase() == "<!DOCTYPE")
                {
                  window.location.replace("/login.htm");
                }       
                else
                    {
                        alert(globalXmlHttp.responseText);
                        document.getElementById('users').focus(); 
                    }
                globalXmlHttp = null;  
            }
            else
                if(globalXmlHttp.status == 403)
                {
                    window.location.replace("/login.htm");
                    globalXmlHttp = null;  
                }       
            
        }
        globalXmlHttp.send(params);
    }
}

function getStrength(str)
{	
	if (str == 5)
		str = 4;
	
	return "/images/bar-" + str + ".png";
}

function removeCheckmark() 
{
    var table = document.getElementById('scanTable').getElementsByTagName("tbody")[0]; 
    var rows = table.rows;

    for (i = 1; i < rows.length; i++) {
    	rows[i].lastChild.removeChild(rows[i].lastChild.lastChild);
    	rows[i].lastChild.appendChild(document.createTextNode(""));
    }
}

function getSecurity(sec) {
	var security;
	
	switch (sec)
	{
	case 0:
		security = "no";
		break;
	case 1:
		security = "wep";
		break;
	case 5:
	case 9:
	case 13:
		security = "wpa";
		break;
	default:
	   // impossible to get here!
		break;
	}
	
	return security;
}

function securityKeyPrompt(secCode) {
	var key;
	
	var wep64RE = new RegExp("^[0-9a-fA-F]{10}$"); // check for hex key, 10 digits long
	var wep64REA = new RegExp("^.{5}$"); // check for ASCII key, 5 digits long
	var wep128RE = new RegExp("^[0-9a-fA-F]{26}$"); // check for hex key, 26 digits long
	var wep128REA = new RegExp("^.{13}$"); // check for ASCII key, 13 digits long
	var wpaREA = new RegExp("^.{8,63}$"); // check for ASCII passphrase, 8-63 characters long
	
	var errMsg;
	var keyInvalid = 0;
	if (secCode == 1 || secCode == 2) {
		do {
			msg = "Please enter your WEP key";
			if (keyInvalid) {
				msg = errMsg + "\r\n" + msg;
			}
			
			key = prompt(msg);
			
			if (key == null) {
				// user hit cancel, so need to go back to main screen and not submit
				// remove check mark also
				
				return "__UFU__";
			} else if (key == "") {
				// user hit enter only, so modify error message to notify user
				keyInvalid = 1;
				errMsg = "No key entered!\r\n";
			} else {
				// key could be valid, check it
				if ((wep64RE.test(key) == false) && (wep64REA.test(key) == false) &&
					(wep128RE.test(key) == false) && (wep128REA.test(key) == false)) {
					keyInvalid = 1;
					errMsg = "WEP key is not the correct length!\r\n";
					errMsg += "Keys must be either:\r\n";
					errMsg += "(a) 10 or 26 hexadecimal digits or\r\n";
					errMsg += "(b) 5 or 13 ASCII characters\r\n";
				} else {
					if ((key.length == 5) || (key.length == 10)) {
 						document.getElementById("sec1").value = '1';
					} else if ((key.length == 13) || (key.length == 26)) {
					    document.getElementById("sec1").value = '2';
					}
					
					keyInvalid = 0;
				}
			}
		} while (keyInvalid);
	} else if (secCode > 1) {
		do {
			msg = "Please enter your passphrase";
			if (keyInvalid) {
				msg = errMsg + "\r\n" + msg;
			}
			
			key = prompt(msg);
			
			if (key == null) {
				// user hit cancel, so need to go back to main screen and not submit
				// remove check mark also
				
				return "__UFU__";
			} else if (key == "") {
				// user hit enter only, so modify error message to notify user
				keyInvalid = 1;
				errMsg = "No passphrase entered!\r\n";
			} else {
				// passphrase could be valid, check it
				if (wpaREA.test(key) == false) {
					keyInvalid = 1;
					errMsg = "WPA passphrase is not the correct length!\r\n";
					errMsg += "Passphrase must be 8-63 characters long.\r\n";
				} else {
					keyInvalid = 0;
				}
			}
		} while (keyInvalid);
	}
	
	return key;
}

function switchNetwork(id, join) {
	if (document.getElementById("rescan").disabled == true) {
		// don't allow users to click any of the network names
		// if we are currently doing a scan
		return;
	}
	
	var networkParam = new Array();
	networkParam = id.split("\020", 3);
 
 	var name = networkParam[0];
	var secCode = networkParam[1];
	var wlanCode = networkParam[2];
	
	if (name == "")
	{
		alert('SSID cannot be left blank!');
		return;
	}
	else if (wlanCode == "undefined")
	{
		alert('Please choose either adhoc or infrastructure');
		return;
	}
	
	removeCheckmark();
	var row = document.getElementById(id);
	if (row != null) {
		// null means that the row doesn't exist
		// only happens when we are entering a SSID manually
		// from the Other Network... dropdown
		row.lastChild.removeChild(row.lastChild.lastChild);
	
		var checkImg = document.createElement("img");
		checkImg.src = "/images/checkmark.png";
		row.lastChild.appendChild(checkImg);
	}
    var data = "wlan=";
     data += wlanCode;
    data += "&ssid="+ name;
	
	var key;
	if (parseInt(secCode)) {
		key = securityKeyPrompt(secCode);
		data += "&key=" + key;
	}

	data += "&sec=";
	
	if(join) 
        data += document.getElementById("sec1").value;
	else
        data += secCode;
	    
 	if (key == "__UFU__") {
		// user hit cancel on the prompt box for the network
		// so assume they didn't want to set the network
		removeCheckmark();
	} else {
  		//document.kickoff.submit();
       newAJAXCommand('nwsw.cgi', testCGIResponse, false, data);		
	}
}

function testCGIResponse(response)
{
    try{
   if(response.substring(0,9).toUpperCase() == "<!DOCTYPE")
   {
      window.location.replace("/login.htm");
   }       
   else
        if(response != null && response != "")
            alert(response);
                    
     }catch(err){alert(""+err);}  
}

function joinNetwork() {
	// copy elements from hidden form and submit them through
	// the normal form
	var id;
	
	id = document.getElementById('ssid1').value + "\020";
	id += document.getElementById('sec1').value + "\020";
	var wlanVal;
	var wlanRadio = document.getElementsByName('wlan1');
	for (i = 0; i < wlanRadio.length; i++) {
		if (wlanRadio[i].checked) {
			wlanVal = 2 - i;
			break;
		}
	}
	
	id += wlanVal;
	switchNetwork(id,true);
}

function userSelectNetwork() {
	// add rows for adhoc/infra selection, text input of ssid and 
	// selector box for security type
	// if security type other than none is chosen, append additional
	// text input field for key/passphrase
	
	otherNetworkExpanded = (otherNetworkExpanded == 1) ? 0 : 1;
	
	if (otherNetworkExpanded) 
	{
   	// need to destroy table back to just button
				
				var table = document.getElementById('scanTable').getElementsByTagName('tfoot')[0];
				var rows = table.rows;
				
				while (rows.length - 1) // length=1 -> stop 
 					table.deleteRow(rows.length - 1);
			}
			else {			
				var tfoot = document.getElementById('scanTable').getElementsByTagName("tfoot")[0];
				
				var row1 = document.createElement("tr");
				row1.setAttribute('style', 'width:9em');
				
				var data1 = document.createElement("td");
				data1.setAttribute('colspan', 3);
				data1.appendChild(document.createTextNode('Adhoc'));
				
				var data2 = document.createElement("td");
				var adhocInput = document.createElement("input");
				adhocInput.setAttribute('type', 'radio');
				adhocInput.setAttribute('name', 'wlan1');
				adhocInput.setAttribute('value', '2');
				adhocInput.setAttribute('onclick', 'adhocSel();');
				data2.appendChild(adhocInput);
				
				row1.appendChild(data1);
				row1.appendChild(data2);
				
				var row2 = document.createElement("tr");
				row2.setAttribute('style', 'width:9em');
				
				var data3 = document.createElement("td");
				data3.setAttribute('colspan', 3);
				data3.appendChild(document.createTextNode('Infrastructure'));
				
				var data4 = document.createElement("td");
				var infraInput = document.createElement("input");
				infraInput.setAttribute('type', 'radio');
				infraInput.setAttribute('name', 'wlan1');
				infraInput.setAttribute('value', '1');
				infraInput.setAttribute('onclick', 'infraSel();');
				data4.appendChild(infraInput);
				
				row2.appendChild(data3);
				row2.appendChild(data4);
				
				var row3 = document.createElement("tr");
				row3.setAttribute('style', 'width:9em');
				var data5 = document.createElement("td");
				data5.setAttribute('colspan', '4');
				data5.appendChild(document.createTextNode("Network Name"));
				row3.appendChild(data5);
				
				var row4 = document.createElement("tr");
				row4.setAttribute('style', 'width:9em');
				var data6 = document.createElement("td");
				data6.setAttribute('colspan', '4');
				var ssidInput = document.createElement("input");
				ssidInput.setAttribute('type', 'text');
				ssidInput.setAttribute('id', 'ssid1');
				ssidInput.setAttribute('name', 'ssid1');
				ssidInput.setAttribute('maxlength', '32');
				data6.appendChild(ssidInput);
				
				row4.appendChild(data6);
				
				var row5 = document.createElement("tr");
				row5.setAttribute('style', 'width:9em');
				var data7 = document.createElement("td");
				data7.setAttribute('colspan', '4');
				var secSel = document.createElement("select");
				secSel.setAttribute('name', 'sec1');
				secSel.setAttribute('id', 'sec1');
				secSel.options[0] = new Option('None', '0');
				secSel.options[1] = new Option('WPA2 Passphrase', '8');
				secSel.options[2] = new Option('WPA Passphrase', '5');
			    secSel.options[3] = new Option('WEP', '1');
			    secSel.options[4] = new Option('WEP 128 bit', '2');
				data7.appendChild(secSel);
				row5.appendChild(data7);
				
				var row6 = document.createElement("tr");
				row6.setAttribute('style', 'width:9em');
				var data8 = document.createElement("td");
				data8.setAttribute('colspan', '3');
				var joinButton = document.createElement("input");
				joinButton.setAttribute('id', 'joinButton');
				joinButton.setAttribute('type', 'button');
				joinButton.setAttribute('value', 'Join');
				joinButton.setAttribute('onclick', 'joinNetwork();');
				data8.appendChild(joinButton);
				row6.appendChild(data8);
				
				tfoot.appendChild(row1);
				tfoot.appendChild(row2);
				tfoot.appendChild(row3);
				tfoot.appendChild(row4);
				tfoot.appendChild(row5);
				tfoot.appendChild(row6);
			}
}

function adhocSel() {
	if (document.getElementById('sec1').options.length == 3) {
		document.getElementById('sec1').remove(2);
	}
}

function infraSel() {
	if (document.getElementById('sec1').options.length == 2) {
		document.getElementById('sec1').options[2] = new Option('WPA/WPA2 Passphrase', '5');	
	}
}

function addScanRow(ssid, sec, str, wlan, connected) {
	var tbody = document.getElementById('scanTable').getElementsByTagName("tbody")[0];
	var row = document.createElement("tr");
	
	var blankImg = document.createElement("img");
	blankImg.src = "/images/blank.png";
	
	row.setAttribute('id', ssid + "\020" + sec + "\020" + wlan);
	row.setAttribute('onmouseover', "this.style.cursor='pointer'");
	row.setAttribute('onclick', 'switchNetwork(id,false);');
	
	var data1 = document.createElement("td");
	data1.setAttribute('style', 'width:10em');
	data1.appendChild(document.createTextNode(ssid));
	
	var data2 = document.createElement("td");
	var secImg = document.createElement("img");
	secImg.src = "/images/lock.png";
	if (sec > 0) {
		data2.appendChild(secImg);
	} else {
		data2.appendChild(blankImg);
	}
	
	var data3 = document.createElement("td");
	var pwrImg = document.createElement("img");
	pwrImg.src = getStrength(str);
	data3.appendChild(pwrImg);
	
	var data4 = document.createElement("td");
	data4.appendChild(blankImg);

	var data5 = document.createElement("td");
	var ckImg = document.createElement("img");
	if(connected)
	    ckImg.src = "/images/checkmark.png";
	else
	    ckImg.src = "/images/blank.png";
	
	data5.appendChild(ckImg);
	
	row.appendChild(data1);
	row.appendChild(data2);
	row.appendChild(data3);
	row.appendChild(data4);
	row.appendChild(data5);
	
	tbody.appendChild(row);
}

function deleteScanTable() 
{
    var table = document.getElementById('scanTable').getElementsByTagName('tbody')[0]; 
    var rows = table.rows;

    while (rows.length - 1) // length=1 -> stop 
        table.deleteRow(rows.length - 1); 
}

function printButtonName()
{
	var textLabel = "Scanning";
	
	for (i = 0; i < scanDots % 4; i++) {
		textLabel += ".";
	}
	
	scanDots++;
	
	document.getElementById("rescan").value = textLabel;
}

function updateStatus(xmlData) 
{	
	var urlPath = window.location.pathname;
	var pageName = urlPath.substring(urlPath.lastIndexOf('/') + 1);

	if (pageName == 'wifi.htm') 
	{
		if (getXMLValue(xmlData, 'scan', 0) === '0') 
		{
			if (currBss != getXMLValue(xmlData, 'count', 0)) 
			{
				if (getXMLValue(xmlData, 'valid', 0) === '0') 
				{
					// current bss returned isn't valid, so issue a request to chip
					if (currBss < 16) {
						// pad 0 before sending to host
						newAJAXCommand('scan.cgi?getBss=0' + currBss.toString(16));
					}
					else 
					{
						newAJAXCommand('scan.cgi?getBss=' + currBss.toString(16));
					}
					
					setTimeout("newAJAXCommand('/muser/wfstatus.xml', updateStatus, false)", 50);
				}
				else 
				{
				    var thisname = getXMLValue(xmlData, 'name', 0);
					if ((thisname != null) && (thisname != ""))
					 
					{
						// don't display hidden networks or the network you are currently
						// connected to
						
					    var checkMark;
                        if((getXMLValue(xmlData, 'name', 0)) != (getXMLValue(xmlData, 'ssid', 0)))
                            checkMark = false;
                        else
                            checkMark = true;
                      
 						addScanRow(getXMLValue(xmlData, 'name', 0), getXMLValue(xmlData, 'privacy', 0), getXMLValue(xmlData, 'strength', 0), getXMLValue(xmlData, 'wlan', 0), checkMark);
					}
					
					currBss++;
					
					// kick off request for next scan entry
					if (currBss < 16) 
					{
						// pad 0 before sending to host
						newAJAXCommand('scan.cgi?getBss=0' + currBss.toString(16));
					}
					else 
					{
						newAJAXCommand('scan.cgi?getBss=' + currBss.toString(16));
					}
					setTimeout("newAJAXCommand('/muser/wfstatus.xml', updateStatus, false)", 50);
				}
			}
			
			if (currBss == getXMLValue(xmlData, 'count', 0)) 
			{
				// we're done here, all scan results posted, so reenable scan button
				document.getElementById("rescan").disabled = false;
				document.getElementById("rescan").value = "Scan for Wireless Networks";
			}
		}
		else {
			printButtonName();
			setTimeout("newAJAXCommand('/muser/wfstatus.xml', updateStatus, false)", 25);
		}
	}
}

function rescanNetwork()
{
	scanDots = 0;
	printButtonName();
	document.getElementById("rescan").disabled = true;
	
	// generate a request to hardware to issue a rescan
	newAJAXCommand('scan.cgi?scan=1');
	
	// delete old table, replace with new table after scan is finished
   deleteScanTable();
	
	currBss = 0; // reset the current bss pointer
	
	setTimeout("newAJAXCommand('/muser/wfstatus.xml', updateStatus, false)", 50);
}

function toggle_vis(id) {
  var e = document.getElementById(id);
  e.style.display = ((e.style.display!='block') ? 'block' : 'none');
}

function buildBanner(name) {

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

function buildMenu(active,ma0,ma1,ma2,ma3,ma4)
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
    <li><a onclick="document.getElementById(\'newpage\').submit(); ">Logout</a></li> \
    <li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\', \'/user/area.htm\'); document.getElementById(\'newpage\').submit();" >Arm/Disarm</a></li> \
    <li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/user/zones.htm\');document.getElementById(\'newpage\').submit(); ">Zones</a></li>\
    <li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/user/outputs.htm\');document.getElementById(\'newpage\').submit(); ">Output Control</a></li>';

    var mcnt = 3;
    
    if(ma2 == 1)
    {
        mcnt++;
        if(active == 4)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/user/history.htm\');document.getElementById(\'newpage\').submit(); ">History</a></li>';
    }
    if(ma1 == 1)
    {
        mcnt++;
        if(active == 5)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/configpins.htm\');document.getElementById(\'newpage\').submit(); ">Users</a></li>';
        mcnt++;
        if(active == 6)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/config6.htm\');document.getElementById(\'newpage\').submit(); ">Email Reporting</a></li>';
        mcnt++;
        if(active == 7)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/config3.htm\');document.getElementById(\'newpage\').submit(); ">SMS Reporting</a></li>';

        mcnt++;
        if(active == 8)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/muser/config2.htm\');document.getElementById(\'newpage\').submit(); ">Voice Reporting</a></li>';

    }
    if(ma0 == 1)
   {
        mcnt++;
        if(active == 9)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config1.htm\');document.getElementById(\'newpage\').submit(); ">Feature Setup</a></li>';
        mcnt++;
        if(active == 10)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config5.htm\');document.getElementById(\'newpage\').submit(); ">Network Settings</a></li>';
        mcnt++;
        if(active == 11)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config7.htm\');document.getElementById(\'newpage\').submit(); ">Output Settings</a></li>';
        mcnt++;
        if(active == 12)
            active = mcnt;
        mstring += '<li><a onclick="document.getElementById(\'newpage\').setAttribute(\'action\',\'/protect/config8.htm\');document.getElementById(\'newpage\').submit(); ">IP Reporting</a></li>';

    }
    mstring += '</ul>';
       d.innerHTML = mstring;
    d.getElementsByTagName('input')[0].setAttribute('value',getSession());
    d.getElementsByTagName('li')[active].className = 'active';
    document.getElementById('w').appendChild(d); 
}

// function called by iPhone to check the number of menus and their names
// authorisation is checked separately by getMenu() which must be in the html as it contains variables
function getMenuNames()
{
  return '["Arm/Disarm","Sensors","Output Control","History","Users","Email","SMS","Voice","Features","Network","Output Settings","IP Report"]';
}

// function called by iPhone to check the icons for menus
// function called by iPhone to check the icons for menus
function getMenuIcons()
{
  return '["lock","pir","lock","clock","users","email","sms","phone","spanner","network","spanner","spanner"]';
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
// 5  /muser/config6		~ma(1)~		//Email
// 6  /muser/config3		~ma(1)~		//sms
// 7  /muser/config2		~ma(1)~		//Voice
// 8  /protect/config1.htm   ~ma(0)~	//Features
// 9  /protect/config5		~ma(0)~		//Network	
//10   /protect/config7		~ma(0)~		//Outputs
//11 /protect/Config8		~ma(0)~		//IP Reporting
function submitMenu(n)
{
  if (n==0)
    document.getElementById('newpage').setAttribute('action','/user/area.htm');
  else if (n==1)
    document.getElementById('newpage').setAttribute('action','/user/zones.htm');
  else if (n==2)
    document.getElementById('newpage').setAttribute('action','/user/outputs.htm');
  else if (n==3)
    document.getElementById('newpage').setAttribute('action','/user/history.htm');
  else if (n==4)
    document.getElementById('newpage').setAttribute('action','/muser/configpins.htm');
  else if (n==5)
    document.getElementById('newpage').setAttribute('action','/muser/config6.htm');
  else if (n==6)
    document.getElementById('newpage').setAttribute('action','/muser/config3.htm');
 else if (n==7)
    document.getElementById('newpage').setAttribute('action','/muser/config2.htm');
  else if (n==8)
    document.getElementById('newpage').setAttribute('action','/protect/config1.htm');
  else if (n==9)
    document.getElementById('newpage').setAttribute('action','/protect/config5.htm');
  else if (n==10)
    document.getElementById('newpage').setAttribute('action','/protect/config7.htm');
  else if (n==11)
    document.getElementById('newpage').setAttribute('action','/protect/config8.htm');
  else if (n==999)
    document.getElementById('newpage').setAttribute('action','/logout.cgi');
  else
    return;

  document.getElementById('newpage').submit();

  return;
}

// function used by iPhone app to setup web page to run in an app
function setAppMode() {
  var e = document.getElementById('ban');
  e.style.display = 'none'; // hide the banner
  var e = document.getElementById('mnu');
  e.style.display = 'none'; // hide the side menu (shows on ipad)
}

//kick off the AJAX Updater
setTimeout("pollAJAX()", 300);
