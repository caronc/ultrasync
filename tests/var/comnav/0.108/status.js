function checkAreaSeq(response)
{
  var curSeq = getXMLValue(response, 'areas').split(',');
  var data;
  var numeric;

  for (var i = 0; i < curSeq.length; i++) {
    var n = parseInt("" + curSeq[i], 10);
    if (n != areaSequence[i]) {
      data = "arsel=" + i;
      newAJAXCommand('/user/status.xml', updateAstate, false, data);
    }
  }
}

function updateAstate(response)
{
  if (response == null)
    return;

  var bank = parseInt(getXMLValue(response, 'abank'), 10);

  areaSequence[bank] = parseInt(getXMLValue(response, 'aseq'), 10);
  bank *= 17;

  for (var i = 0; i < 17; i++) {
    areaStatus[bank + i] = getXMLValue(response, 'stat' + i);
  }

  sysStatus = getXMLValue(response, 'sysflt').split('\r\n');

  return bank;
}

function updateSystemDisplay(updating)
{
  if (areaCount < 2)
    return;

  var stat = document.getElementById('a0'); // gets the div
  var bgtype = 'bg-grn';
  if (stat == null)
    return;

  if (allpriority == 1 || allpriority == 4)
    bgtype = 'bg-red';
  else
  if (allpriority == 2)
    bgtype = 'bg-blu';
  else
  if (allpriority == 3)
    bgtype = 'bg-yel';
  else
  if (allpriority == 5)
    bgtype = 'bg-gry';

  var buttons = stat.getElementsByTagName('button');
  if (allAway) {
    buttons[0].className = 'ba bg-red';
    buttons[1].className = 'bs bg-gry';
  } else if (allStay) {
    buttons[0].className = 'ba bg-gry';
    buttons[1].className = 'bs bg-yel';
  } else {
    buttons[0].className = 'ba bg-gry';
    buttons[1].className = 'bs bg-gry';
  }
  if (allChime) {
    if (buttons[3].className != 'bc bg-blu') {
      buttons[3].className = 'bc bg-blu';
      cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,'comm=80&data0=2&data2=1&data1=255')";
      buttons[3].setAttribute('onclick', cmd);
    }
  } else {
    if (buttons[3].className != 'bc bg-gry') {
      buttons[3].className = 'bc bg-gry';
      cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false,'comm=80&data0=2&data2=1&data1=255')";
      buttons[3].setAttribute('onclick', cmd);
    }
  }
  if (updating)
    systemString = systemStates[1];
  else
  if (sysStatus.length > 1) {
    allSequence++;
    if (allSequence >= (sysStatus.length - 1))
      allSequence = 0;
    systemString = sysStatus[allSequence];
  } else {
    systemString = systemStates[0];
  }

  if (stat.getElementsByTagName('h2')[0].innerHTML != systemString) {
    stat.getElementsByTagName('h2')[0].innerHTML = systemString;
    stat.firstChild.className = bgtype; // for h1 element
  } else
  if (stat.firstChild.className != bgtype) {
    stat.firstChild.className = bgtype;
  }
}

function updateAllAreas()
{
  allAway = true;
  allStay = true;
  allChime = true;
  allpriority = 6;

  for (var i = 0; i < areaNames.length; i++) {
    if (areaNames[i] != "!")
      updateArea(i + 1);
  }

  updateSystemDisplay(false);
  setTimeout("updateAllAreas()", 1500);
}

function buildArea(area)
{
  var mask = 255;
  var start = 0;
  if (area != 0) {
    mask = (0x01 << ((area - 1) % 8));
    start = (Math.floor((area - 1) / 8));
  }
  var div1 = document.createElement("div");
  div1.id = ("a" + area);
  div1.className = 'box';
  div1.innerHTML =
    '<h1></h1> \
        <h2></h2> \
        <button type="button" class="ba"><div class="bi"></div>'+areaLanguage[0]+'</button> \
        <button type="button" class="bs"><div class="bi"></div>'+areaLanguage[1]+'</button> \
        <button type="button" class="bo"><div class="bi"></div>'+areaLanguage[2]+'</button> \
        <button type="button" class="bc"><div class="bi"></div>'+areaLanguage[3]+'</button>';

  if (area == 0)
    div1.getElementsByTagName('h1')[0].innerHTML = miscLabels[0];
  else
    div1.getElementsByTagName('h1')[0].innerHTML = areaNames[area - 1];

  var cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false," + "'comm=80&data0=2&data2=17&data1=" + mask + "')";
  div1.getElementsByTagName('button')[0].setAttribute('onclick', cmd);
  var cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false," + "'comm=80&data0=2&data2=18&data1=" + mask + "')";
  div1.getElementsByTagName('button')[1].setAttribute('onclick', cmd);
  var cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false," + "'comm=80&data0=2&data2=16&data1=" + mask + "')";
  div1.getElementsByTagName('button')[2].setAttribute('onclick', cmd);
  var cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false," + "'comm=80&data0=2&data2=1&data1=" + mask + "')";
  div1.getElementsByTagName('button')[3].setAttribute('onclick', cmd);
  document.getElementById('at').appendChild(div1);

  areaDisplay.push(0);
  if (area == 0)
    updateSystemDisplay(true);
  else
    updateArea(area);
}

function updateArea(area)
{
  try {
    var stat = document.getElementById('a' + area); // gets the div
    if (stat == null)
      return;
    var buttons = stat.getElementsByTagName('button');
    var i = area - 1;
    var areaString = "";
    var bgtype = 'bg-grn';
    var byteindex = (Math.floor(i / 8) * 17);
    var mask = (0x01 << (i % 8));
    var starm = parseInt(areaStatus[byteindex], 10);
    var stpartial = parseInt(areaStatus[byteindex + 1], 10);
    var stchime = parseInt(areaStatus[byteindex + 15], 10);
    var stexit1 = parseInt(areaStatus[byteindex + 7], 10);
    var stexit2 = parseInt(areaStatus[byteindex + 8], 10);
    var cmd;


    if ((parseInt(areaStatus[byteindex + 3], 10) & mask) != 0 ||
      (parseInt(areaStatus[byteindex + 4], 10) & mask) != 0 ||
      (parseInt(areaStatus[byteindex + 5], 10) & mask) != 0 ||
      (parseInt(areaStatus[byteindex + 6], 10) & mask) != 0) {
      allpriority = 1;
      bgtype = "bg-red";
    } else
    if ((parseInt(areaStatus[byteindex + 11], 10) & mask) != 0 ||
      (parseInt(areaStatus[byteindex + 12], 10) & mask) != 0 ||
      (parseInt(areaStatus[byteindex + 13], 10) & mask) != 0 ||
      (parseInt(areaStatus[byteindex + 14], 10) & mask) != 0 ||
      (sysStatus != null && sysStatus.length > 1)) {
      if (allpriority != 1)
        allpriority = 2;
      bgtype = "bg-blue";
    } else
    if ((parseInt(areaStatus[byteindex + 10]) & mask) != 0 || (stpartial & mask) != 0) {
      if (allpriority > 3)
        allpriority = 3;

      bgtype = "bg-yel";
    } else
    if ((starm & mask) != 0) {
      if (allpriority > 4)
        allpriority = 4;

      bgtype = "bg-red";
    } else
    if ((parseInt(areaStatus[byteindex + 2], 10) & mask) == 0) {
      if (allpriority > 5)
        allpriority = 5;

      bgtype = "bg-gry";
    }


    while (areaString == "") {
      if (areaDisplay[i] >= areaStates.length) {
        var maxCount;

        if (areaCount > 1)
          maxCount = (areaStates.length);
        else
          maxCount = (areaStates.length + sysStatus.length);

        if (areaDisplay[i] >= maxCount) {
          if (((stexit1 & mask) != 0) || ((stexit2 & mask) != 0))
            areaDisplay[i] = 3;
          else
            areaDisplay[i] = 0;
        } else {
          areaString = sysStatus[areaDisplay[i] - areaStates.length];
          if (areaString == "No System Faults") {
            areaString = systemStates[0];
          }
          areaDisplay[i]++;
        }
      } else {
        var st = parseInt(areaStatus[areaDisplay[i] + byteindex], 10);
 
        if ((st & mask) != 0) {
          if ((areaDisplay[i] != 2) || ((starm & mask) == 0 && (stpartial & mask) == 0)) {
            areaString = areaStates[areaDisplay[i]];
          }
          if (areaDisplay[i] == 7)
            areaDisplay[i]++;
        } else if (areaDisplay[i] == 2 && (starm & mask) == 0 && (stpartial & mask) == 0) {
          areaString = areaLanguage[4];
        }

        areaDisplay[i]++;
      }
    }

    if (stat.getElementsByTagName('h2')[0].innerHTML != areaString) {
      stat.getElementsByTagName('h2')[0].innerHTML = areaString;
      stat.firstChild.className = bgtype; // for h1 element
    } else
    if (stat.firstChild.className != bgtype) {
      stat.firstChild.className = bgtype;
    }

    if ((starm & mask) != 0) {
      buttons[0].className = 'ba bg-red';
      buttons[1].className = 'bs bg-gry';
      allStay = false;
    } else if ((stpartial & mask) != 0) {
      buttons[0].className = 'ba bg-gry';
      buttons[1].className = 'bs bg-yel';
      allAway = false;
    } else {
      buttons[0].className = 'ba bg-gry';
      buttons[1].className = 'bs bg-gry';
      allStay = false;
      allAway = false;

    }

    if ((stchime & mask) != 0) {
      if (buttons[3].className != 'bc bg-blu') {
        buttons[3].className = 'bc bg-blu';
        cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false," + "'comm=80&data0=2&data2=1&data1=" + mask + "')";
        buttons[3].setAttribute('onclick', cmd);
      }
    } else {
      allChime = false;
      if (buttons[3].className != 'bc bg-gry') {
        buttons[3].className = 'bc bg-gry';
        cmd = "newAJAXCommand('/user/keyfunction.cgi', cgiResponse, false," + "'comm=80&data0=2&data2=1&data1=" + mask + "')";
        buttons[3].setAttribute('onclick', cmd);
      }
    }
  } catch (err) {
    alert("" + err);
  }
}

function buildAreas()
{
  /* Build this html to insert areas into:
  <div class="main" id="at">
  </div>
  */
  var d = document.createElement("div");

  d.id = ("at");
  d.className = 'main';
  document.getElementById('w').appendChild(d);
  areaCount = 0;

  for (var i = 0; i < areaNames.length; i++)
    if (areaNames[i] != "!")
      areaCount++;
  if (areaCount > 1)
    buildArea(0)
  var j = 1;

  for (; j < areaNames.length + 1; j++) {
    if (areaNames[j - 1] == "")
      areaNames[j - 1] = config7NamesLab[3 + j];
    if (areaNames[j - 1] != "!")
      buildArea(j)
    else
      areaDisplay.push(0);
  }
}

function cgiResponse(responseText)
{
  try {
    if (responseText != null) {
      var bank = updateAstate(responseText);
      for (var i = 0; i < 8; i++) {
        if (areaNames[i + bank] != "!")
          updateArea(i + 1);
      }
    }
  } catch (err) {
    alert("" + err);
  }
  newAJAXCommand('/user/seq.xml', checkAreaSeq, false);
}

function pollSequence()
{
  newAJAXCommand('/user/seq.xml', checkAreaSeq, false);
  setTimeout("pollSequence()", 5500);
}

function checkZoneSeq(response)
{
  if (response == null)
    return;

  var curSeq = getXMLValue(response, 'zones').split(',');
  var data;
  var numeric;

  for (var i = 0; i < curSeq.length; i++) {
    var n = parseInt("" + curSeq[i], 10);
    if (n != zoneSequence[i]) {
      data = "state=" + i;
      newAJAXCommand('/user/zstate.xml', updateZstate, false, data);
    }
  }
  setTimeout("newAJAXCommand('/user/seq.xml', checkZoneSeq, false)", 5500);
}

function updateZstate(response)
{
  if (response == null)
    return;

  var bank = parseInt(getXMLValue(response, 'zstate'), 10);
  zoneSequence[bank] = parseInt(getXMLValue(response, 'zseq'), 10);
  zoneStatus[bank] = getXMLValue(response, 'zdat').split(',');
}

function updateAllZones()
{
  for (var i = 0; i < zoneNames.length; i++) {
    if (zoneNames[i] != "!")
      updateZone(i + 1);
  }
  setTimeout("updateAllZones()", 1500);
}

function buildZone(zone)
{
  var div1 = document.createElement("div");
  div1.id = ("z" + zone);
  div1.className = 'box';
  div1.innerHTML =
    '<h1></h1> \
    <h2></h2> \
    <button type="button" class="bb" ><div class="bi"></div>'+zoneLanguage[2]+'</button>' // \
    //  <button type="button" class="bc"><div class="bi"></div>Chime</button>';
  div1.getElementsByTagName('h1')[0].innerHTML = zoneNames[zone - 1];
  document.getElementById('zt').appendChild(div1);

  zoneDisplay.push(0);
  updateZone(zone);
}

function updateZone(zone)
{
  if (zone == null)
    return;

  try {
    var stat = document.getElementById('z' + zone); // gets the div
    var buttons = stat.getElementsByTagName('button');

    var i = zone - 1;
    var zoneString = "";
    var bgtype = 'bg-grn';
    var byteindex = Math.floor(i / 16);
    var mask = (0x01 << (i % 16));
    var st;
    var cmd;

    if ((parseInt(zoneStatus[5][byteindex], 10) & mask) != 0)
      bgtype = "bg-red";
    else
    if ((parseInt(zoneStatus[1][byteindex], 10) & mask) != 0 ||
      (parseInt(zoneStatus[2][byteindex], 10) & mask) != 0 ||
      (parseInt(zoneStatus[6][byteindex], 10) & mask) != 0 ||
      (parseInt(zoneStatus[7][byteindex], 10) & mask) != 0)
      bgtype = "bg-blue";
    else
    if ((parseInt(zoneStatus[3][byteindex], 10) & mask) != 0 || (parseInt(zoneStatus[4][byteindex], 10) & mask) != 0)
      bgtype = "bg-yel";
    else
    if ((parseInt(zoneStatus[0][byteindex], 10) & mask) != 0)
      bgtype = "bg-gry";

    while (zoneString == "") {
      if (zoneDisplay[i] >= zoneStates.length)
        zoneDisplay[i] = 0;

      st = parseInt(zoneStatus[zoneDisplay[i]][byteindex], 10);

      if ((st & mask) != 0) {
        zoneString = zoneStates[zoneDisplay[i]];
      } else
      if (zoneDisplay[i] == 0) {
        zoneString = zoneLanguage[1];
      }
      zoneDisplay[i]++;
    }

    if (stat.getElementsByTagName('h2')[0].innerHTML != zoneString) {
      stat.getElementsByTagName('h2')[0].innerHTML = zoneString;
      stat.firstChild.className = bgtype; // for h1 element
    } else
    if (stat.firstChild.className != bgtype) {
      stat.firstChild.className = bgtype;
    }
    /*
    st = parseInt(zoneStatus[9][byteindex],10);
    if((st & mask)!= 0)
    {
        if (buttons[1].className != 'bc bg-blu')
        {
            buttons[1].className = 'bc bg-blu';
            cmd = "newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+  "'comm=82&data0="  + (zone-1) +"')";
            buttons[1].setAttribute('onclick', cmd);
        }
    }
    else
    {
        if (buttons[1].className != 'bc bg-gry')
        {
            buttons[1].className = 'bc bg-gry';
            cmd = "newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false,"+  "'comm=82&data0="  + (zone-1) +"')";
            buttons[1].setAttribute('onclick', cmd);
        }
    }
    */
    st = parseInt(zoneStatus[3][byteindex], 10);
    if ((st & mask) != 0) {
      if (buttons[0].className != 'bc bg-yel') {
        buttons[0].className = 'bb bg-yel';
        cmd = "newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false," + "'comm=82&data0=" + (zone - 1) + "')";
        buttons[0].setAttribute('onclick', cmd);
      }
    } else {
      if (buttons[0].className != 'bc bg-gry') {
        buttons[0].className = 'bb bg-gry';
        cmd = "newAJAXCommand('/user/zonefunction.cgi', zoneCGIresponse, false," + "'comm=82&data0=" + (zone - 1) + "')";
        buttons[0].setAttribute('onclick', cmd);
      }
    }
  } catch (err) {
    alert("" + err);
  }
}

function buildZones()
{
  /* Build this html to insert zones into:
  <div class="main" id="zt">
  </div>
  */
  var d = document.createElement("div");
  d.id = ("zt");
  d.className = 'main';
  document.getElementById('w').appendChild(d);

  for (var j = 1; j < zoneNames.length + 1; j++) {
    if (zoneNames[j - 1] == "")
      zoneNames[j - 1] = zoneLanguage[0] + ' ' + j;
    if (zoneNames[j - 1] != "!")
      buildZone(j)
    else
      zoneDisplay.push(0);
  }
}

function zoneCGIresponse(responseText)
{
  try {
    if (responseText != null) {
      updateZstate(responseText);
      for (var i = 0; i < zoneNames.length; i++) {
        if (zoneNames[i] != "!")
          updateZone(i + 1);
      }
    }
  } catch (err) {
    alert("" + err);
  }
}

function changeIndex(qty)
{
  var current;

  if (qty > 0 && document.getElementById('nextb').className == 'bg-gry')
    return;
  if (qty < 0 & document.getElementById('prevb').className == 'bg-gry')
    return;

  current = parseInt("" + index, 10);
  mr = parseInt("" + mostRecent, 10);

  if (qty < 0)
    direction = 'dec';
  else
    direction = 'inc';

  current += qty;

  if (current >= count)
    current -= count;
  if (current < 0)
    current += count;

  index = current;

  newAJAXCommand('/user/history.xml', updateHistory, false, "event=" + index);
}

function updateHistory(responseText)
{
  var current;
  var mr;
  var old;

  try {
    if (responseText != null) {
      current = getXMLValue(responseText, 'cur');
      mr = getXMLValue(responseText, 'last');
      old = getXMLValue(responseText, 'old');
      if (current == "" + index || "" + index == "65535" || "" + index == "65534") {
        if ("" + index == "65535")
          index = mr;
        else
        if ("" + index == "65534")
          index = old;

        document.getElementById('event').value = getXMLValue(responseText, 'evrsp') /* + "\nindex= "+current+"\nRecent= "+mr+"\noldest= "+old*/ ;
        if (current == mr)
          document.getElementById('nextb').setAttribute('class', 'bg-gry');
        else
          document.getElementById('nextb').setAttribute('class', 'bg-blu');

        if (current == old)
          document.getElementById('prevb').setAttribute('class', 'bg-gry');
        else
          document.getElementById('prevb').setAttribute('class', 'bg-blu');
        mostRecent = mr;

      } else
        setTimeout("checkHistory()", 500);

    } else
      setTimeout("checkHistory()", 500);

  } catch (err) {
    alert("" + err);
  }
}

function checkHistory()
{
  if (ajaxList.length == 0) {
    newAJAXCommand('/user/history.xml', updateHistory, false, "event=" + index);
  } else
    setTimeout("checkHistory()", 500);
}

function buildOutputs()
{
  /* Build this html to insert zones into:
  <div class="main" id="zt">
  </div>
  */
  var d = document.createElement("div");
  d.id = ("ot");
  d.className = 'main';
  document.getElementById('w').appendChild(d);
  buildOutput(1);
  buildOutput(2);
}

function buildOutput(output)
{
  var div1 = document.createElement("div");
  div1.id = ("o" + output);
  div1.className = 'box';
  div1.innerHTML =
    '<h1></h1> \
    <button type="button" class="bb" ><div class="bi"></div>On</button>\
    <button type="button" class="bc"><div class="bi"></div>Off</button>';
  div1.getElementsByTagName('h1')[0].innerHTML = outputLanguage[2] + ' ' + output;
  document.getElementById('ot').appendChild(div1);
}
