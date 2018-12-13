/**
* Ajax.js
*
* Collection of Scripts to allow in page communication from browser to (struts) server
* ie can reload part instead of full page
*
* How to use
* ==========
* 1) Call retrieveURL from the relevant event on the HTML page (e.g. onclick)
* 2) Pass the url to contact (e.g. Struts Action) and the name of the HTML form to post
* 3) When the server responds ...
*		 - the script loops through the response , looking for <span id="name">newContent</span>
* 		 - each <span> tag in the *existing* document will be replaced with newContent
*
* NOTE: <span id="name"> is case sensitive. Name *must* follow the first quote mark and end in a quote
*		 Everything after the first '>' mark until </span> is considered content.
*		 Empty Sections should be in the format <span id="name"></span>
*/

//global variables
var expandedElements = new Array();

/**
* Get the contents of the URL via an Ajax call
* url - to get content from (e.g. /struts-ajax/sampleajax.do?ask = COMMAND_NAME_1)
* nodeToOverWrite - when callback is made
* formID - which form values will be posted up to the server as part
*					of the request (can be null)
*/
function retrieveURL(url,form, classOfElementsToReload) {

	//get the (form based) params to push up as part of the get request
	var params = Form.serialize(form,true);

	new Ajax.Request(url, {
		method: 'post', evalScripts:true, parameters:params,
		onSuccess: function(transport) {
			elements = splitTextIntoElements(transport.responseText, classOfElementsToReload);
			//Use these elements to update the page
			replaceExistingWithNewHtml(elements, classOfElementsToReload);
		}
	});
}

/**
* Splits the text into <span> elements or elements which class is classOfElementsToReload
* @param the text to be parsed
* @return array of elements - this array can contain nulls
*/
function splitTextIntoElements(textToSplit, classOfElementsToReload) {


	if (classOfElementsToReload == null || classOfElementsToReload == "") {
		//Split the document
		var returnElements = textToSplit.split("</span>")

		//Process each of the elements 
		for (var i = returnElements.length - 1; i >= 0; --i) {

			//Remove everything before the 1st span
			var spanPos = returnElements[i].indexOf("<span");

			//if we find a match , take out everything before the span
			if (spanPos > 0) {
				var subString = returnElements[i].substring(spanPos);
				returnElements[i] = subString;

			}
		}
	} else {
		var node = getDomNodeFromStr(textToSplit);
		// returnElements = node.getElementsByClassName(classOfElementsToReload);
		returnElements = node.select('.'+classOfElementsToReload);
	}

	return returnElements;
}

/*
* Replace html elements in the existing (ie viewable document)
* with new elements (from the ajax requested document)
* WHERE they have the same name AND are <span> elements or are of the class classOfElementsToReload
* @param newTextElements (output of splitTextIntoElements)
*					in the format <span id = name>texttoupdate
*/
function replaceExistingWithNewHtml(newTextElements, classOfElementsToReload) {

	if (classOfElementsToReload == null || classOfElementsToReload == "") {
		//loop through newTextElements
		for (var i = newTextElements.length-1; i>=0; --i) {

			//check that this begins with <span
			if (newTextElements[i].indexOf("<span")>-1) {

				//get the name - between the 1st and 2nd quote mark
				var startNamePos = newTextElements[i].indexOf('"')+1;
				var endNamePos = newTextElements[i].indexOf('"',startNamePos);
				var name = newTextElements[i].substring(startNamePos,endNamePos);

				//get the content - everything after the first > mark
				var startContentPos = newTextElements[i].indexOf('>')+1;
				var elemContent = newTextElements[i].substring(startContentPos);

				//Now update the existing Document with this element
				
				/*
				//check that this element exists in the document
				if (document.getElementById(name)) {

					//alert("Replacing Element:"+name);
					document.getElementById(name).innerHTML = elemContent;
				} else {
					//alert("Element:"+name+"not found in existing document");
				}
				*/
				
				var elem = $(name);
				//check that this element exists in the document
				if (elem) {

					//alert("Replacing Element:"+name);
					elem.update(elemContent);
				} else {
					//alert("Element:"+name+"not found in existing document");
				}
			}
		}
	} else {
		//loop through newTextElements
		var id;
		var elem;
		var elemContent;
		var className;
		for (var i = newTextElements.length-1; i>=0; --i) {

			elem = newTextElements[i];

			//check that the element has class name classOfElementsToReload
			if (elem.hasClassName(classOfElementsToReload)) {

				id = elem.id;
				elemContent = elem.innerHTML;
				elemValue = elem.value;
				className = elem.className;
				elem = $(id); // element in the current document

				//check that this element exists in the document
				if (elem) {
					// elem.innerHTML = elemContent;
					elem.update(elemContent);
					elem.value = elemValue;
					elem.className = className;
				} else {
					//alert("Element:"+name+"not found in existing document");
				}
			}
		}
		// Expand elements that were expanded
		for (var i = 0; i < expandedElements.length; i++) {
			id = expandedElements[i].id;
			elem = $(id); // element in the current document
			if (elem) {
				if (elem.hasClassName("collapsed")) {
					elem.removeClassName("collapsed");
					elem.addClassName("expanded");
				}
			}
		}
	}
}


/**
* Allow to do an "AJAX submit".
* A normal submit would reload the entire page. That's not what we want.
* This funtion allows to load just a part of a page after the "submit".
* It is based on a modified version of the "getFormAsURL" function of ajax.js
* @param container the id of the part of the page that needs o be reloaded
* @param url the Struts action that needs to be executed
* @param form the form where the data needs to be picked up from
**/
function ajaxUpdateContainerWithStrutsAction(url, form, container) {
	$('preloader').show();
	$('content').hide();
	var params = Form.serialize(form,true);
	new Ajax.Updater(container, url, {
		onComplete:function() {
			$('preloader').hide();
			$('content').show();
		}, evalScripts:true, method:'post', parameters:params
	});
}

/**
*
**/
function ajaxUpdateElementsWithStrutsAction(url, form, classOfElementsToReload) {
	// expandedElements = document.getElementsByClassName('expanded');
	expandedElements == $$('.expanded');
	retrieveURL(url,form,classOfElementsToReload);
}

function getDomNodeFromStr(str) {
	var node = document.createElement("div");
	node.innerHTML = str;
	var node2 = new Element('div');
	node2.textContent = str;
	return node;
}


/**
*
*  AJAX IFRAME METHOD (AIM)
*  http://www.webtoolkit.info/
*
**/

AIM = {

	frame : function(c) {
	
		var n = 'f' + Math.floor(Math.random() * 99999);
		var d = document.createElement('DIV');
		d.innerHTML = '<iframe width="0" height="0" src="about:blank" id="'+n+'" name="'+n+'" onload="AIM.loaded(\''+n+'\')"></iframe>';
		document.body.appendChild(d);

		var i = document.getElementById(n);
		/*
		var iframe = $('hiddeniframe');
		iframe.setAttribute('onload',"AIM.loaded('hiddeniframe')");
		*/
		if (c && typeof(c.onComplete) == 'function') {
			i.onComplete = c.onComplete;
		}
		return n;
	},

	form : function(f, name) {
		f.setAttribute('target', name);
	},

	submit : function(f, c) {
		AIM.form(f, AIM.frame(c));
		if (c && typeof(c.onStart) == 'function') {
			return c.onStart();
		} else {
			return true;
		}
	},

	loaded : function(id) {
		var i = document.getElementById(id);
		if (i.contentDocument) {
			var d = i.contentDocument;
		} else if (i.contentWindow) {
			var d = i.contentWindow.document;
		} else {
			var d = window.frames[id].document;
		}
		if (d.location.href == "about:blank") {
			return;
		}

		if (typeof(i.onComplete) == 'function') {
			i.onComplete(d.body.innerHTML);
		}
	}

}
