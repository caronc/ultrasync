
	var areaStates = new Array(
		
	"Armed Away", 
	"Armed Stay", 
	"Ready",
	"Fire Alarm",
	"Burg Alarm",
	"Panic Alarm",
	"Medical Alarm",
	"Exit Delay",
	"Exit Delay 2",
	"Entry Delay",
	"Zone Bypass",
	"Zone Trouble",
	"Zone Tamper",
	"Zone Low Battery",
	"Zone Supervision",
	""
);

  var histNames = new Array(
  	
  	"Oldest",
  	"Prev",
  	"Next",
  	"Latest"
  	
  );
  
  var zoneStates = new Array(
  	"Not Ready", 
  	"Tamper", 
  	"Trouble",
  	"Bypass",
  	"Inhibited",
  	"Alarm",
  	"Low Battery",
  	"Supervision Fault",
  	"",
  	"",
  	"",
  	"",
  	"",
  	""
  	);
  	
var outputLanguage = new Array(
	"On",
	"Off",
	"Output",
	"ON",
	"OFF"
	
);

var h1Names = new Array(
	"Save Config",
	"Feature Setup",
	"Voice Reporting",
	"SMS Reporting",
	"",
	"Network Settings",
	"Email Reporting",
	"Configure Outputs",
	"IP Reporting",
	"Configure Users"
	
);
var config1NamesLab = new Array(
	"Enable Zone Doubling",
	"Enable Ans Machine Defeat"
);

var config1NamesPar = new Array(
	"NX-595E",
	"Rings to Answer:",
	"Start Zone:",
	"Installer Name:",
	"Service Number:",
	"Device ID:",
	"Firmware:",
	"Hardware:",
	"Bootload:",
	"Web Version:",
	"Voice:",
	"Language:",
	""
	
);
var config1NamesHeaders = new Array(
	"GMT Offset:",
	"Daylight Saving Time Start:",
	"Daylight Saving Time End:",
	""
	
);
var config2NamesHeaders = new Array(
	"Voice Phone 1:",
	"Voice Phone 2:",
	"Voice Phone 3:",
	"Dial Attemps:",
	"Voice 1 Events:"
	
);
var config3NamesHeaders = new Array(
	"SMS Phone 1:",
	"SMS Phone 2:",
	"SMS Phone 3:",
	"SMS Server:",
	"SMS 1 Events:",
	"SMS 2 Events:",
	"SMS 3 Events:"
	
);
var config6NamesPar = new Array(
	"Email 1 Address:",
	"Email 2 Address:",
	"Email 3 Address:"
);

var config6NamesHeaders = new Array(
	"Email 1 Events:",
	"Email 2 Events:",
	"Email 3 Events:",
	"Return Address:"
);
var config8NamesHeaders = new Array(
	"Serial Number:",
	"Receiver 1 Format:",
	"Receiver 1 Address:",
	"Receiver 1 Port:",
	"Receiver 1 Account:",
	"Receiver 1 Supervision Time:",
	"Receiver 1 Number:",
	"Receiver 1 Line Number:",
	"Use PSTN for Failover:",
	"Receiver 1 Selectors:",
	"Receiver 2 Format:",
	"Receiver 2 Address:",
	"Receiver 2 Port:",
	"Receiver 2 Account:",
	"Receiver 2 Supervision Time:",
	"Receiver 2 Number:",
	"Receiver 2 Line Number:",
	"Receiver 2 Selectors:"
);

var reportCategories = new Array(
	"Alarms",
	"Restores",
	"Opening/Closing",
	"Bypass",
	"Zone Trouble",
	"Power Trouble",
	"Tampers",
	"Test Reports",
	"System Trouble",
	"Failure To Report",
	"Sensor Trouble",
	"Start/End Program Mode ",
	"Cancel",
	"Recent Close",
	"Reserved",
	"Reserved"
	
);
   
 var  gmtNames  = new Array(
    "Disabled",
    "13",
    "+12",
    "+11",
    "+10 Sydney",
    "+9",
    "+8",
    "+7",
    "+6",
    "+5",
    "+3",
    "+4",
    "+2",
    "+1 Brussels",
    "0 (GMT)",
    "-1",
    "-2",
    "-3",
    "-4",
    "-5 New York",
    "-6 Chicago",
    "-7 Denver",
    "-8 Los Angelos",
    "-9",
    "-10",
    "-11",
    "-12" 	
 	);  
 	
 	var months = new Array(
 		"Disabled",
 		"Jan",
 		"Feb",
 		"Mar",
 		"Apr",
 		"May",
 		"Jun",
 		"Jul",
 		"Aug",
 		"Sep",
 		"Oct",
 		"Nov",
 		"Dec"
 		
 	) 
 	
 	var weeks = new Array(
 		"First Sunday",
 		"Second Sunday",
 		"Third Sunday",
 		"Fourth Sunday",
 		"Last Sunday"
 	) ;   
 	
 var config5NamesPar = new Array(
 		"NX-595E",
 		"MAC Address:",
 		"Host Name:",
 		"IP Address",
 		"Gateway",
 		"Subnet Mask",
 		"Primary DNS",
 		"Secondary DNS",
 		"SSL Port:",
 		"Web Access Passcode",
 		"Web Access Server 1",
 		"Web Access Server 2",
 		"DLX900 Port:"
 		
 	) ;   
 	
 	var config5NamesLab = new Array(
 		"Enable DHCP",
  		"Enable Ping",
 		"Enable NTP Server Time Updates",
 		"Enable DLX900 Server",
 		"Enable Web Access"

 		
 	) ; 
 	
 	 var PINNamesPar = new Array(
 		"NX-595E",
 		"Select a User:",
 		"Displaying User:",
 		"User Name:",
 		"PIN:",
 		"Pin Digits:"
 		
 	) ;   
 	 	 var PINNamesH2 = new Array(
 		"User Authority:",
 		"User Partitions:"
 		
 	) ;   
 	
 	var pinButtons = new Array(
 		
	"Clear User",
	"Save User"
	
 	) ;  
 	
	var pinLabels = new Array( 
		
	"Arm Only",
	"Schedule",
	"Master",
	"Arm/Disarm",
	"Bypass",
	"Report",
	"Reserved",
	"Reserved",
	"Partition 1", 
	"Partition 2", 
	"Partition 3", 
	"Partition 4", 
	"Partition 5", 
	"Partition 6", 
	"Partition 7", 
	"Partition 8"
	
 	 	) ;  
 		     
var config7NamesHeaders = new Array(
	"Output 1 Programming:",
	"Output 1 Options:",
	"Output 1 Partitions:",
	"Output 1 Schedule:",
	"Output 1 Schedule Times:",
	"Output 1 Schedule Days:",
	"Output 2 Programming:",
	"Output 2 Options:",
	"Output 2 Partitions:",
	"Output 2 Schedule:",
	"Output 2 Schedule Times:",
	"Output 2 Schedule Days:"
);

var config7NamesPar = new Array(
	"NX-595E",
	"Activation Event:",
	"Activation Time:",
	"Open Hour:",
	"Open Minute:",
	"Close Hour:",
	"Close Minute:" 		
 	) ;   
var config7NamesLab = new Array( 	
 	"Minutes",
 	"Latch",
 	"Code Reset",
 	"Invert",
 	"Partition 1",
 	"Partition 2",
 	"Partition 3",
 	"Partition 4",
 	"Partition 5",
 	"Partition 6",
 	"Partition 7",
 	"Partition 8",
 	"Open Schedule",
 	"Close Schedule",
 	"Sun",
 	"Mon",
 	"Tue",
 	"Wed",
 	"Thu",
 	"Fri",
 	"Sat"
      	) ;  
 
 var config7Options = new Array( 	     	
	"Zone Burg Alarm",
	"Fire Alarm",
	"Panic Alarm",
	"Zone Trouble Alarm",
	"Zone Tamper Alarm",
	"Burg Siren",
	"Fire Siren",
	"Any Siren",
	"Bypassed Zone",
	"AC Fail",
	"Low Battery",
	"Duress Alarm",
	"Aux 1 Keypad Alarm",
	"Aux 2 Keypad Alarm",
	"Panic Keypad Alarm",
	"Key Press Tamper",
	"Auto Test",
	"Alarm Memory",
	"Entry",
	"Exit",
	"Entry or Exit",
	"Armed",
	"Disarmed",
	"Ready",
	"Not Ready",
	"Fire",
	"Fire Trouble",
	"Chime",
	"Expander Trouble",
	"Battery test",
	"Open Schedule",
	"Closed Schedule",
	"Listen in",
	"Line Seizure",
	"Reserved",
	"Fail to Communicate",
	"Telephone Line Fault",
	"Program Mode",
	"Download mode",
	"Reserved",
	"Output Over-current",
	"Box Tamper",
	"Siren Tamper",
	"Any Zone Trouble",
	"Any Zone Tamper",
	"Any Zone Fault",
	"Any Zone Alarm",
	"Manual Control",
	"Code Entry",
	"Fob Function 1",
	"Fob Function 2",
	"Reserved",
	"Reserved",
	"Output 1 Trigger",
	"Output 2 Trigger",
	"Reserved",
	"Reserved"
     	) ;     
     	
 var nameEditStrings = new Array(
	"Edit Names Then Click Save",
	"Save",
	"Copy",
	"Copy All",
	"Partition Names",
	"Partition",
	"Zone Names",
	"ZN",
	"Output Names",
	"OP",
	"Entry Message",
	"Exit Message"
);      

var results = new Array(
	"Success!",									    //0
	"Busy Copying Names. Try Again Momentarily!",   //1
	 "Copying Changed Names!",						//2
	 "Busy Copying Names. Try Again Momentarily!",  //3
	 "Copying All Names!",							//4
	 "Busy Copying Names. Try Again Momentarily!"	//5
	 
	 
);
var formatOptions = new Array(
	"disabled",
	"UltraConnect",
	"OH CID IP format",
	"OH SIA IP format"
);        
var alerts = new Array(
	"Account code must be no more than 6 digits",
	"Acount code must only contain digits\nfrom 0-9 and A-F"
);     
var miscLabels = new Array(
	"All Partitions"
)  