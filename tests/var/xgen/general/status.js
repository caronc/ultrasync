var areaStatesByte=[6,4,0,16,20,18,22,8,10,12,64,66,68,70,72,14,56];function checkAreaSeq(response){if(response==null)return;var curSeq=null;try{curSeq=JSON.parse(response)}catch(ex){}if(curSeq==null){window.location.replace("/login.htm");return}var seqarray=curSeq.area;var data;for(var i=0;i<seqarray.length&&i<areaSequence.length;i++){if(seqarray[i]!=areaSequence[i]){data="arsel="+i;newAJAXCommand("/user/status.json",updateAstate,false,data)}}}function updateAstate(response){if(response==null)return;var as=null;try{as=JSON.parse(response)}catch(ex){}if(as==null){window.location.replace("/login.htm");return}var bank=as.abank;areaSequence[bank]=as.aseq;areaStatus[bank]=as.bankstates;var ss=as.system;convertNames(ss);sysStatus=ss;return bank}function updateSystemDisplay(updating){if(areaCount<2)return;var stat=document.getElementById("a0");var bgtype="bg-grn";if(stat==null)return;if(allpriority==1||allpriority==4)bgtype="bg-red";else if(allpriority==2)bgtype="bg-blu";else if(allpriority==3)bgtype="bg-yel";else if(allpriority==5)bgtype="bg-gry";var buttons=stat.getElementsByTagName("button");if(allAway){buttons[0].className="ba bg-red";buttons[1].className="bs bg-gry"}else if(allStay){buttons[0].className="ba bg-gry";buttons[1].className="bs bg-yel"}else{buttons[0].className="ba bg-gry";buttons[1].className="bs bg-gry"}if(allChime){if(buttons[3].className!="bc bg-blu"){buttons[3].className="bc bg-blu";cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,'fnum=11&start=0&mask=0')";buttons[3].setAttribute("onclick",cmd)}}else{if(buttons[3].className!="bc bg-gry"){buttons[3].className="bc bg-gry";cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,'fnum=10&start=0&mask=0')";buttons[3].setAttribute("onclick",cmd)}}if(updating)systemString=statusStrings[0];else if(sysStatus.length>=1){allSequence++;if(allSequence>=sysStatus.length)allSequence=0;systemString=sysStatus[allSequence]}else systemString=statusStrings[1];var h2v=stat.getElementsByTagName("h2")[0];if(h2v.innerHTML!=systemString){h2v.innerHTML=systemString;stat.firstChild.className=bgtype;h2v=stat.getElementsByTagName("h2")[0]}else if(stat.firstChild.className!=bgtype){stat.firstChild.className=bgtype}if(h2v.clientHeight>60)h2v.setAttribute("style","line-height: 28px");else if(h2v.clientHeight<50)h2v.setAttribute("style","line-height: 56px")}function updateAllAreas(){allAway=true;allStay=true;allChime=true;allpriority=6;for(var i=0;i<areaNames.length;i++){if(areaNames[i]!="!")updateArea(i+1)}updateSystemDisplay(false);setTimeout("updateAllAreas()",1500)}function buildArea(area){var mask=0;var start=0;if(area!=0){mask=1<<(area-1)%8;start=Math.floor((area-1)/8)}var div1=document.createElement("div");div1.id="a"+area;div1.className="box";div1.innerHTML='<h1></h1>     <h2></h2>     <button type="button" class="ba" ><div class="bi"></div>'+statusStrings[10]+'</button>     <button type="button" class="bs"><div class="bi"></div>'+statusStrings[11]+'</button>     <button type="button" class="bo"><div class="bi"></div>'+statusStrings[12]+'</button>     <button type="button" class="bc"><div class="bi"></div>'+statusStrings[6]+"</button>";if(mask==0)div1.getElementsByTagName("h1")[0].innerHTML=statusStrings[3];else div1.getElementsByTagName("h1")[0].innerHTML=areaNames[area-1];var cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,"+"'fnum=15&start="+start+"&mask="+mask+"')";div1.getElementsByTagName("button")[0].setAttribute("onclick",cmd);var cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,"+"'fnum=1&start="+start+"&mask="+mask+"')";div1.getElementsByTagName("button")[1].setAttribute("onclick",cmd);var cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,"+"'fnum=0&start="+start+"&mask="+mask+"')";div1.getElementsByTagName("button")[2].setAttribute("onclick",cmd);var cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,"+"'fnum=10&start="+start+"&mask="+mask+"')";div1.getElementsByTagName("button")[3].setAttribute("onclick",cmd);document.getElementById("at").appendChild(div1);areaDisplay.push(0);if(area==0)updateSystemDisplay(true);else updateArea(area)}function updateArea(area){try{var stat=document.getElementById("a"+area);if(stat==null)return;var buttons=stat.getElementsByTagName("button");var i=area-1;var bankState=areaStatus[Math.floor(i/8)];var areaString="";var bgtype="bg-grn";var byteindex=Math.floor(i/8)*19;var mask=1<<i%8;var starm=parseInt(bankState.substring(6,8),16);var stpartial=parseInt(bankState.substring(4,6),16);var stchime=parseInt(bankState.substring(36,38),16);var stexit1=parseInt(bankState.substring(8,10),16);var stexit2=parseInt(bankState.substring(10,12),16);var stnight=parseInt(bankState.substring(52,54),16);var stwalk=parseInt(bankState.substring(54,56),16);var cmd;if((parseInt(bankState.substring(16,18),16)&mask)!=0||(parseInt(bankState.substring(18,20),16)&mask)!=0||(parseInt(bankState.substring(20,22),16)&mask)!=0||(parseInt(bankState.substring(22,24),16)&mask)!=0){allpriority=1;bgtype="bg-red"}else if((parseInt(bankState.substring(66,68),16)&mask)!=0||(parseInt(bankState.substring(68,70),16)&mask)!=0||(parseInt(bankState.substring(70,72),16)&mask)!=0||(parseInt(bankState.substring(72,74),16)&mask)!=0||stwalk&mask||sysStatus!=null&&sysStatus.length>=1){if(allpriority!=1)allpriority=2;bgtype="bg-blue"}else if((parseInt(bankState.substring(64,66),16)&mask)!=0||(stpartial&mask)!=0){if(allpriority>3)allpriority=3;bgtype="bg-yel"}else if((starm&mask)!=0){if(allpriority>4)allpriority=4;bgtype="bg-red"}else if((parseInt(bankState.substring(0,2),16)&mask)==0){if(allpriority>5)allpriority=5;bgtype="bg-gry"}while(areaString==""){if(areaDisplay[i]>=areaStates.length){var maxCount;if(areaCount>1)maxCount=areaStates.length;else maxCount=areaStates.length+sysStatus.length;if(areaDisplay[i]>=maxCount){if((stexit1&mask)!=0||(stexit2&mask)!=0)areaDisplay[i]=3;else areaDisplay[i]=0}else{areaString=sysStatus[areaDisplay[i]-areaStates.length];areaDisplay[i]++}}else{var st=parseInt(bankState.substring(areaStatesByte[areaDisplay[i]],areaStatesByte[areaDisplay[i]]+2),16);if((st&mask)!=0){if(areaDisplay[i]!=2||(starm&mask)==0&&(stpartial&mask)==0){if(areaDisplay[i]==2&&(stwalk&mask)!=0){areaString=setNames[18]}else areaString=areaStates[areaDisplay[i]];if((stpartial&mask)!=0){if(areaDisplay[i]==1||areaDisplay[i]==7||areaDisplay[i]==8){if((stnight&mask)!=0){areaString+=" - "+voicetokens[103]}else if((parseInt(bankState.substring(14,16),16)&mask)!=0){areaString+=" - "+voicetokens[88]}}}}if(areaDisplay[i]==7)areaDisplay[i]++}else if(areaDisplay[i]==2&&(starm&mask)==0&&(stpartial&mask)==0){st=parseInt(bankState.substring(2,4),16);if((st&mask)==0)areaString=masterStrings[21];else areaString=masterStrings[20]}areaDisplay[i]++}}var h2v=stat.getElementsByTagName("h2")[0];if(h2v.innerHTML!=areaString){h2v.innerHTML=areaString;stat.firstChild.className=bgtype;h2v=stat.getElementsByTagName("h2")[0]}else if(stat.firstChild.className!=bgtype){stat.firstChild.className=bgtype}if(h2v.clientHeight>60)h2v.setAttribute("style","line-height: 28px");else if(h2v.clientHeight<50)h2v.setAttribute("style","line-height: 56px");if((starm&mask)!=0){buttons[0].className="ba bg-red";buttons[1].className="bs bg-gry";allStay=false}else if((stpartial&mask)!=0){buttons[0].className="ba bg-gry";if((stnight&mask)==0)buttons[1].className="bs bg-yel";else buttons[1].className="bs bg-red";allAway=false}else{buttons[0].className="ba bg-gry";buttons[1].className="bs bg-gry";allStay=false;allAway=false}if((stchime&mask)!=0){if(buttons[3].className!="bc bg-blu"){buttons[3].className="bc bg-blu";cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,"+"'fnum=11&start="+Math.floor((area-1)/8)+"&mask="+mask+"')";buttons[3].setAttribute("onclick",cmd)}}else{allChime=false;if(buttons[3].className!="bc bg-gry"){buttons[3].className="bc bg-gry";cmd="newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,"+"'fnum=10&start="+Math.floor((area-1)/8)+"&mask="+mask+"')";buttons[3].setAttribute("onclick",cmd)}}}catch(err){alert(""+err)}}function buildAreas(){var d=document.createElement("div");d.id="at";d.className="main";document.getElementById("w").appendChild(d);areaCount=0;for(var i=0;i<areaNames.length;i++)if(areaNames[i]!="!")areaCount++;if(areaCount>1)buildArea(0);if(areaCount==0){var div1=document.createElement("div");div1.id="area0";div1.innerHTML="<h1>"+statusStrings[2]+"</h1>";document.getElementById("at").appendChild(div1)}else{var j=1;for(;j<areaNames.length+1;j++){if(areaNames[j-1]=="")areaNames[j-1]=statusStrings[4]+" "+j;if(areaNames[j-1]!="!")buildArea(j);else areaDisplay.push(0)}}}function cgiResponse(responseText){try{if(responseText!=null){var bank=updateAstate(responseText);for(var i=0;i<8;i++){if(areaNames[i+bank]!="!")updateArea(i+1)}}}catch(err){alert(""+err)}newAJAXCommand("/user/seq.json",checkAreaSeq,false)}function pollSequence(){newAJAXCommand("/user/seq.json",checkAreaSeq,false);setTimeout("pollSequence()",5500)}function checkZoneSeq(response){if(response==null)return;var curSeq=null;try{curSeq=JSON.parse(response)}catch(ex){}if(curSeq==null){window.location.replace("/login.htm");return}var zonearray=curSeq.zone;var data;for(var i=0;i<zonearray.length&&i<zoneSequence.length;i++){if(zonearray[i]!=zoneSequence[i]){data="state="+i;newAJAXCommand("/user/zstate.json",updateZstate,false,data)}}setTimeout("newAJAXCommand('/user/seq.json', checkZoneSeq, false)",5500)}function updateZstate(response){if(response==null)return;var zs=null;try{zs=JSON.parse(response)}catch(ex){}if(zs==null){window.location.replace("/login.htm");return}var bank=zs.zbank;zoneSequence[bank]=zs.zseq;zoneStatus[bank]=zs.bankstates;var ss=zs.system;convertNames(ss);sysStatus=ss}function updateAllZones(){for(var i=0;i<zoneNames.length;i++){if(zoneNames[i]!="!")updateZone(i+1)}setTimeout("updateAllZones()",1500)}function buildZone(zone){var div1=document.createElement("div");div1.id="z"+zone;div1.className="box";var controls='<h1></h1>     <h2></h2>     <button type="button" class="bb btn-zn" ><div class="bi"></div>'+statusStrings[5]+'</button>     <button type="button" class="bc btn-zn"><div class="bi"></div>'+statusStrings[6]+"</button>";if(ismaster==1||isinstaller==1){controls+='<button type="button" class="bn btn-zn"><div class="bi"></div>'+statusStrings[13]+"</button>"}div1.innerHTML=controls;div1.getElementsByTagName("h1")[0].innerHTML=zoneNames[zone-1];document.getElementById("zt").appendChild(div1);zoneDisplay.push(0);updateZone(zone)}function updateZone(zone){try{var stat=document.getElementById("z"+zone);var buttons=stat.getElementsByTagName("button");var i=zone-1;var zoneString="";var bgtype="bg-grn";var byteStart=Math.floor(i/8)*2;var mask=1<<i%8;var st;var cmd;var wt=parseInt(zoneStatus[12].substring(byteStart,byteStart+2),16);if((parseInt(zoneStatus[5].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[8].substring(byteStart,byteStart+2),16)&mask)!=0)bgtype="bg-red";else if((parseInt(zoneStatus[1].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[2].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[6].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[7].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[12].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[14].substring(byteStart,byteStart+2),16)&mask)!=0)bgtype="bg-blue";else if((parseInt(zoneStatus[3].substring(byteStart,byteStart+2),16)&mask)!=0||(parseInt(zoneStatus[4].substring(byteStart,byteStart+2),16)&mask)!=0)bgtype="bg-yel";else if((parseInt(zoneStatus[0].substring(byteStart,byteStart+2),16)&mask)!=0)bgtype="bg-gry";if((parseInt(zoneStatus[8].substring(byteStart,byteStart+2),16)&mask)!=0)zoneString=zoneStates[12];else if((parseInt(zoneStatus[12].substring(byteStart,byteStart+2),16)&mask)!=0)zoneString=statusStrings[7];else while(zoneString==""){if(zoneDisplay[i]>=zoneStates.length)zoneDisplay[i]=0;st=parseInt(zoneStatus[zoneDisplay[i]].substring(byteStart,byteStart+2),16);if((st&mask)!=0){zoneString=zoneStates[zoneDisplay[i]]}else if(zoneDisplay[i]==0){if((wt&mask)!=0){zoneDisplay[i]++;continue}zoneString=statusStrings[7]}zoneDisplay[i]++}var h2v=stat.getElementsByTagName("h2")[0];if(h2v.innerHTML!=zoneString){h2v.innerHTML=zoneString;stat.firstChild.className=bgtype}else if(stat.firstChild.className!=bgtype){stat.firstChild.className=bgtype}if(h2v.clientHeight>60)h2v.setAttribute("style","line-height: 28px");else if(h2v.clientHeight<50)h2v.setAttribute("style","line-height: 56px");st=parseInt(zoneStatus[9].substring(byteStart,byteStart+2),16);if((st&mask)!=0){if(buttons[1].className!="bc btn-zn bg-blu"){buttons[1].className="bc btn-zn bg-blu";cmd="newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+"'cmd=6&opt=0&zone="+(zone-1)+"')";buttons[1].setAttribute("onclick",cmd)}}else{if(buttons[1].className!="bc btn-zn bg-gry"){buttons[1].className="bc btn-zn bg-gry";cmd="newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+"'cmd=6&opt=1&zone="+(zone-1)+"')";buttons[1].setAttribute("onclick",cmd)}}st=parseInt(zoneStatus[3].substring(byteStart,byteStart+2),16);if((st&mask)!=0){if(buttons[0].className!="bb btn-zn bg-yel"){buttons[0].className="bb btn-zn bg-yel";cmd="newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+"'cmd=5&opt=0&zone="+(zone-1)+"')";buttons[0].setAttribute("onclick",cmd)}}else{if(buttons[0].className!="bb btn-zn bg-gry"){buttons[0].className="bb btn-zn bg-gry";cmd="newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+"'cmd=5&opt=1&zone="+(zone-1)+"')";buttons[0].setAttribute("onclick",cmd)}}if(buttons.length==3){st=parseInt(zoneStatus[16].substring(byteStart,byteStart+2),16);if((st&mask)!=0){if(buttons[2].className!="bn btn-zn bg-blu"){buttons[2].className="bn btn-zn bg-blu";cmd="newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+"'cmd=9&opt=0&zone="+(zone-1)+"')";buttons[2].setAttribute("onclick",cmd)}}else{if(buttons[2].className!="bn btn-zn bg-gry"){buttons[2].className="bn btn-zn bg-gry";cmd="newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+"'cmd=9&opt=1&zone="+(zone-1)+"')";buttons[2].setAttribute("onclick",cmd)}}}}catch(err){alert(""+err)}}function buildZones(){var za=false;var d=document.createElement("div");d.id="zt";d.className="main";document.getElementById("w").appendChild(d);for(var j=1;j<zoneNames.length+1;j++){if(zoneNames[j-1]=="")zoneNames[j-1]=statusStrings[8]+" "+j;if(zoneNames[j-1]!="!"){buildZone(j);za=true}else zoneDisplay.push(0)}if(!za){var div1=document.createElement("div");div1.id="zone0";div1.innerHTML="<h1>"+statusStrings[9]+"</h1>";document.getElementById("zt").appendChild(div1)}}function zoneCGIresponse(responseText){try{if(responseText!=null){updateZstate(responseText);for(var i=0;i<zoneNames.length;i++){if(zoneNames[i]!="!")updateZone(i+1)}}}catch(err){alert(""+err)}}function changeIndex(oper){var start=0;var param="count=10&start=";if(oper=="new"){start=65535}else if(oper=="old"){start=events.oldest+9;if(start>=events.max)start-=events.max}else if(oper=="inc"){start=events.events[0].id;for(var n=0;n<10;n++){if(start==events.last){n=10;start=65535}else start++;if(start>=events.max)start-=events.max}}else{if(events.events[events.events.length-1].id!=events.oldest){start=events.events[events.events.length-1].id-1;if(start<0)start=events.max-1}else return}param+=start;param+="&type="+getFilter();newAJAXCommand("/user/api/events.cgi",historyResponse,false,param)}function parseEvents(response){try{events=JSON.parse(response)}catch(ex){}if(events.error!=null){window.location.replace("/login.htm");return}if(events.events.length==0){alert(historyStrings[6]);return}var lines="";var div1=document.createElement("div");div1.id="events";var e=document.getElementById("events");e.parentNode.replaceChild(div1,e);for(var i=0;i<events.events.length;i++){var decoded="";var index=i;try{decoded=decodeURIComponent(events.events[index].text)}catch(err){}var linesplit=decoded.split("  ");lines="";for(var s=0;s<linesplit.length;s++){if(s!=0)lines+="\n";lines+=linesplit[s]}var div1=document.createElement("div");div1.id="e"+i;div1.className="box";var vc;if(!isLan)vc=events.events[index].clip;var cols=35;var controls="";if(vc!=null){lines+="\nPress to Play Video";controls+='<a id="ref" style="text-decoration:none" href="http://dummy/intercept/clip?'+vc+'" >'}controls+='<textarea id="event" rows="6" cols="'+cols+'" readonly="readonly">'+lines+"</textarea>";if(vc!=null)controls+="</a>";div1.innerHTML=controls;document.getElementById("events").appendChild(div1)}if(events.events[0].id==events.last){document.getElementById("nextb").setAttribute("class","bg-gry btn-hf")}else{document.getElementById("nextb").setAttribute("class","bg-blu btn-hf")}if(events.events[events.events.length-1].id==events.oldest){document.getElementById("prevb").setAttribute("class","bg-gry btn-hf")}else{document.getElementById("prevb").setAttribute("class","bg-blu btn-hf")}}function historyResponse(response){parseEvents(response)}function dateLoad(){if(!isLoaded)return;var date=document.getElementById("startdate").value;if(date!=""){var intdate=RFC3339dateToInt(date);intdate*=86400;var param="count=10&date="+intdate;param+="&type="+getFilter();newAJAXCommand("/user/api/events.cgi",historyResponse,false,param)}}function getFilter(){return document.getElementById("f1").selectedIndex}function loadHistory(){var div1=document.createElement("div");div1.id="events";var e=document.getElementById("events");e.parentNode.replaceChild(div1,e);var param="count=10";param+="&type="+getFilter();newAJAXCommand("/user/api/events.cgi",historyResponse,false,param)}function buildHistoryPage(){var e=document.getElementById("old");e.innerHTML=historyStrings[0];e=document.getElementById("prevb");e.innerHTML=historyStrings[1];e=document.getElementById("nextb");e.innerHTML=historyStrings[2];e=document.getElementById("new");e.innerHTML=historyStrings[3];e=document.getElementById("evtitle");e.innerHTML=historyStrings[7];e=document.getElementById("datesel");e.innerHTML=historyStrings[8]+":";var control='<label id="fsel" class="ls">'+historyStrings[12]+":</label>";control+='<select id="f1" class="rs" onchange="resetdate();loadHistory();">';control+='<option selected="true">'+historyStrings[9]+"</option>";control+="<option>"+historyStrings[10]+"</option>";control+="<option>"+historyStrings[11]+"</option>";control+="</select>";e=document.getElementById("filter");e.innerHTML=control}function resetdate(){document.getElementById("startdate").value=intToDate(currentDate)}/*EOF*/