var timeOutMS=1e4;var profwin;var globalXmlHttp;var userAccess;var cameraAccess;var installerAccess;var region;var ajaxList=new Array;var scanDots=0;var currBss=0;var otherNetworkExpanded=1;var AjaxIsIdle=true;var lastAjaxPoll;function newAJAXCommand(url,container,repeat,data){var newAjax=new Object;var theTimer=new Date;newAjax.url=url;newAjax.container=container;newAjax.repeat=repeat;newAjax.ajaxReq=null;if(data==null)data="sess="+getSession();else{data="sess="+getSession()+"&"+data}if(window.XMLHttpRequest){newAjax.ajaxReq=new XMLHttpRequest;newAjax.ajaxReq.open(data==null?"GET":"POST",newAjax.url,true);newAjax.ajaxReq.send(data)}else if(window.ActiveXObject){newAjax.ajaxReq=new ActiveXObject("Microsoft.XMLHTTP");if(newAjax.ajaxReq){newAjax.ajaxReq.open(data==null?"GET":"POST",newAjax.url,true);newAjax.ajaxReq.send(data)}}AjaxIsIdle=false;newAjax.lastCalled=theTimer.getTime();ajaxList.push(newAjax);if(theTimer.getTime()-lastAjaxPoll>1e3){pollAJAX()}}function pollAJAX(){var curAjax=new Object;var theTimer=new Date;var elapsed;var nd=new Date;lastAjaxPoll=nd.getTime();for(i=ajaxList.length;i>0;i--){curAjax=ajaxList.shift();if(!curAjax){continue}elapsed=theTimer.getTime()-curAjax.lastCalled;if(curAjax.ajaxReq.readyState==4&&curAjax.ajaxReq.status==200&&curAjax.ajaxReq.responseText.substring(0,9).toUpperCase()!="<!DOCTYPE"){if(typeof curAjax.container=="function"){try{curAjax.container(curAjax.ajaxReq.responseText)}catch(err){}}else if(typeof curAjax.container=="string"){try{document.getElementById(curAjax.container).innerHTML=curAjax.ajaxReq.responseText}catch(err){}}curAjax.ajaxReq.abort();curAjax.ajaxReq=null;if(curAjax.repeat)newAJAXCommand(curAjax.url,curAjax.container,curAjax.repeat);continue}else if(curAjax.ajaxReq.readyState==4&&curAjax.ajaxReq.status==200){window.location.replace("/login.htm");return}if(elapsed>timeOutMS){if(typeof curAjax.container=="function"){curAjax.container(null)}else{}curAjax.ajaxReq.abort();curAjax.ajaxReq=null;if(curAjax.repeat)newAJAXCommand(curAjax.url,curAjax.container,curAjax.repeat);continue}ajaxList.push(curAjax)}if(ajaxList.length==0)AjaxIsIdle=true;else AjaxIsIdle=false;setTimeout("pollAJAX()",50)}function getXMLValue(xmlData,field){result="";if(xmlData!=null){tag="<"+field+">";var s=xmlData.indexOf(tag);var e=xmlData.indexOf("</"+field+">");if(s>=0&&e>s)result=xmlData.substring(s+tag.length,e)}return result}function hideElement(whichElement){document.getElementById(whichElement).style.display="none"}function viewElement(whichElement){document.getElementById(whichElement).style.display="inline"}function textToNumber(text){var i;var mult=1;var result=0;for(i=0;i<text.length/2;i++){result+=parseInt(text.substring(2*i,2*i+2),16)*mult;mult*=256}return result}function numberToText(text,digits){var number=parseInt(text);if(number<0){number+=Math.pow(256,digits/2)}var hexnumber=number.toString(16).toUpperCase();var result="";if(hexnumber=="NAN")return result;while(hexnumber.length<digits)hexnumber="0"+hexnumber;for(i=hexnumber.length;i>0;i-=2)result+=hexnumber.substring(i-2,i);return result}function RFC3339dateAndTimeToInt(value){fs=value.indexOf("-",0);ss=value.indexOf("-",fs+1);sp=value.indexOf(" ",0);fc=value.indexOf(":",0);sc=value.indexOf(":",fc+1);year=parseInt(value.substring(0,fs),10);if(year<100)year+=2e3;month=parseInt(value.substring(fs+1,ss),10);day=parseInt(value.substring(ss+1,sp),10);hr=parseInt(value.substring(sp+1,fc),10);if(sc==-1){sec=0;min=parseInt(value.substring(fc+1,value.length),10)}else{sec=parseInt(value.substring(sc+1),10);min=parseInt(value.substring(fc+1,sc),10)}if(sec<0||sec>59)sec=0;return Date.UTC(year,month-1,day,hr,min,sec)/1e3}function RFC3339dateToInt(value){asa=value.split("-");year=parseInt(asa[0],10);month=parseInt(asa[1],10);day=parseInt(asa[2],10);if(year<100)year+=2e3;result=Date.UTC(year,month-1,day)/864e5;return result}function intToDate(k){d=new Date(k*864e5);resp=d.getUTCFullYear()+"-"+pad(d.getUTCMonth()+1)+"-"+pad(d.getUTCDate());return resp}function timeToInt(value){fc=value.indexOf(":",0);hr=parseInt(value.substring(0,fc),10);min=parseInt(value.substring(fc+1),10);return hr*60+min}function intToTime(dt){d=new Date(dt*6e4);resp=pad(d.getUTCHours())+":"+pad(d.getUTCMinutes());return resp}function intToDateAndTime(dt){var d=new Date(dt*1e3);resp=d.getUTCFullYear()+"-"+pad(d.getUTCMonth()+1)+"-"+pad(d.getUTCDate())+" "+pad(d.getUTCHours())+":"+pad(d.getUTCMinutes())+":"+pad(d.getUTCSeconds());return resp}function pad(n){return n<10?"0"+n:n}function justRFC3339Date(dt){var d=new Date(dt*1e3);resp=d.getUTCFullYear()+"-"+pad(d.getUTCMonth()+1)+"-"+pad(d.getUTCDate());return resp}function df(element){e=document.getElementById(element);e.select();e.focus()}function testCGIResponse(response){try{if(response==null||response==""){alert(masterStrings[0]+"\n"+masterStrings[1])}else if(response.substring(0,9).toUpperCase()=="<!DOCTYPE"){window.location.replace("/login.htm")}else alert(response)}catch(err){}}function toggle_vis(id){var e=document.getElementById(id);e.style.display=e.style.display!="block"?"block":"none"}function buildBanner(name){var d=document.createElement("div");d.id="ban";d.setAttribute("class","ban");d.innerHTML='<button type="button" class="mnu-btn" onclick="toggle_vis(\'mnu\');">'+masterStrings[2]+"</button><p></p>";d.getElementsByTagName("p")[0].innerHTML=name;document.getElementById("w").appendChild(d)}function buildMenu(active,ma0,ma1,ma2,ma3,ma4,ma5){userAccess=ma1;cameraAccess=ma5;installerAccess=ma0;var d=document.createElement("div");d.id="mnu";var mstring='<form method="post" id="newpage"  action="/logout.cgi" name="newpage1">     <input type="hidden" id="sess1" name="sess"/>     </form>     <ul class="nav">     <li><a onclick="document.getElementById(\'newpage\').submit(); ">'+masterStrings[3]+"</a></li>     <li><a onclick=\"document.getElementById('newpage').setAttribute('action', '/user/area.htm'); document.getElementById('newpage').submit();\" >"+masterStrings[4]+"</a></li>     <li><a onclick=\"document.getElementById('newpage').setAttribute('action','/user/zones.htm');document.getElementById('newpage').submit(); \">"+masterStrings[5]+"</a></li>";var mcnt=2;if(ma5==1){mcnt++;if(active==3)active=mcnt;mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action','/muser/video.htm');document.getElementById('newpage').submit(); \">"+masterStrings[6]+"</a></li>"}if(ma4==1){mcnt++;if(active==4)active=mcnt;mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action', '/user/rooms.htm'); document.getElementById('newpage').submit();\" >"+masterStrings[7]+"</a></li>"}if(ma2==1){mcnt++;if(active==5)active=mcnt;mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action','/user/history.htm');document.getElementById('newpage').submit(); \">"+masterStrings[8]+"</a></li>"}mcnt++;if(active==6)active=mcnt;if(ma1==1){mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action','/user/configpins.htm');document.getElementById('newpage').submit(); \">"+masterStrings[9]+"</a></li>"}else mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action','/user/configpins.htm');document.getElementById('newpage').submit(); \">"+masterStrings[10]+"</a></li>";if(ma3==1){mcnt++;if(active==7)active=mcnt;mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action','/muser/config2.htm');document.getElementById('newpage').submit(); \">"+masterStrings[11]+"</a></li>"}if(ma0==1){mcnt++;if(active==8)active=mcnt;mstring+="<li><a onclick=\"document.getElementById('newpage').setAttribute('action','/protect/config1.htm');document.getElementById('newpage').submit(); \">"+masterStrings[12]+"</a></li>"}mstring+="</ul>";d.innerHTML=mstring;d.getElementsByTagName("input")[0].setAttribute("value",getSession());d.getElementsByTagName("li")[active].className="active";document.getElementById("w").appendChild(d)}function getMenuNames(){if(userAccess==1)return'["'+masterStrings[4]+'","'+masterStrings[5]+'","'+masterStrings[6]+'","'+masterStrings[7]+'","'+masterStrings[8]+'","'+masterStrings[9]+'","'+masterStrings[11]+'","'+masterStrings[12]+'"]';else return'["'+masterStrings[4]+'","'+masterStrings[5]+'","'+masterStrings[6]+'","'+masterStrings[7]+'","'+masterStrings[8]+'","'+masterStrings[10]+'","'+masterStrings[11]+'","'+masterStrings[12]+'"]'}function getMenuIcons(){return'["lock","pir","camera","door","clock","users","settings","settings"]'}function submitMenu(n){if(n==0)document.getElementById("newpage").setAttribute("action","/user/area.htm");else if(n==1)document.getElementById("newpage").setAttribute("action","/user/zones.htm");else if(n==2)document.getElementById("newpage").setAttribute("action","/muser/video.htm");else if(n==3)document.getElementById("newpage").setAttribute("action","/user/rooms.htm");else if(n==4)document.getElementById("newpage").setAttribute("action","/user/history.htm");else if(n==5)document.getElementById("newpage").setAttribute("action","/user/configpins.htm");else if(n==6)document.getElementById("newpage").setAttribute("action","/muser/config2.htm");else if(n==7)document.getElementById("newpage").setAttribute("action","/protect/config1.htm");else if(n==999)document.getElementById("newpage").setAttribute("action","/logout.cgi");else return;document.getElementById("newpage").submit();return}function setAppMode(){var e=document.getElementById("play");if(e!=null)e.style.display="inline-block";var e=document.getElementById("ban");e.style.display="none";var e=document.getElementById("mnu");e.style.display="none"}setTimeout("pollAJAX()",300);function removeBadCharacters(thestring,theregexp){while(thestring.match(theregexp)!=null){var badone=thestring.indexOf(thestring.match(theregexp));thestring=thestring.substring(0,badone)+thestring.substring(badone+1)}return thestring}function checkNameEntry(nid,length){var newData=document.getElementById(nid).value;if(newData.length>length){alert("Data limited to "+length+" characters!");document.getElementById(nid).value=newData.substring(0,length);return true}return false}function imageLoaded(camera){setTimeout(function(){updateCameraLink(camera)},2e3)}function updateCameraLink(camera){var si=document.getElementById("img"+camera);if(si!=null){var link=si.getAttribute("src");if(link=="javascript: void(0)"){var address=cameraDB.cameras[camera].ip;link="http://"+address+"/cgi-bin/viewer/video.jpg"}else{var links=link.split("&time=");link=links[0]+"&time="+(new Date).getTime()}si.onload=function(){imageLoaded(camera)};si.onerror=function(){imageLoaded(camera)};si.setAttribute("src",link)}}function buildCamera(camera){var div1=document.createElement("div");var name=cameraDB.cameras[camera-1].name;if(name=="")name="Camera "+camera;var address=cameraDB.cameras[camera-1].ip;var link="http://"+address+"/cgi-bin/viewer/video.jpg";div1.id="camera"+camera;div1.className="box";div1.innerHTML="<h1>"+name+'</h1><img src="javascript: void(0)" id="img'+camera+'" width="274" height="200"/>';document.getElementById("ct").appendChild(div1)}function buildCameras(islan){var ca=false;var d=document.createElement("div");d.id="ct";d.className="main";document.getElementById("w").appendChild(d);if(!islan)for(var j=1;j<17;j++){if(cameraDB.cameras[j-1].MAC!=null&&cameraDB.cameras[j-1].MAC!=""){buildCamera(j);ca=true}}if(!ca){var div1=document.createElement("div");div1.id="zone0";if(!islan){div1.innerHTML="<h1>"+masterStrings[14]+"</h1>";document.getElementById("ct").appendChild(div1);div1=document.createElement("div");div1.id="zone1";div1.innerHTML="<h1>"+masterStrings[15]+"</h1>"}else div1.innerHTML="<h1>"+masterStrings[16]+"</h1>";document.getElementById("ct").appendChild(div1)}}function zoneCGIresponse(responseText){try{if(responseText!=null){updateZstate(responseText);for(var i=0;i<zoneNames.length;i++){if(zoneNames[i]!="!")updateZone(i+1)}}}catch(err){}}function nameSortUsers(){usersData.users.sort(function(a,b){var nameA=a.lname.toLowerCase()+a.fname.toLowerCase();var nameB=b.lname.toLowerCase()+b.fname.toLowerCase();if(nameA<nameB)return-1;if(nameA>nameB)return 1;return 0})}function numberSortUsers(){usersData.users.sort(function(a,b){var numA=a.user;var numB=b.user;return numA-numB})}function convertUserNames(usersObject){for(var i=0;i<usersObject.users.length;i++){try{usersObject.users[i].fname=decodeURIComponent(usersObject.users[i].fname)}catch(err){}try{usersObject.users[i].lname=decodeURIComponent(usersObject.users[i].lname)}catch(err){}}}function convertNames(namearray){var e;for(var i=0;i<namearray.length;i++){try{namearray[i]=decodeURIComponent(namearray[i])}catch(err){alert(namearray[i])}}}function encode_utf8(s){return unescape(encodeURIComponent(s))}function decode_utf8(s){return s}function convertHexToString(input){var hex=input.match(/[\s\S]{2}/g)||[];var output="";for(var i=0,j=hex.length;i<j;i++){output+="%"+("0"+hex[i]).slice(-2)}output=decodeURIComponent(output);return output}function getNodeName(index){var namet=jnodeData[index].dename;if(namet=="")namet=typeNames[index];return namet}/*EOF*/