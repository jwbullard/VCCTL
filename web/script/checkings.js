/*extern $, Ajax */

/**
* Registrations functions
**/

function checkEmailValidity(emailField) {
    /**
     * Disabling this function for now
     */
    /*
	var regexp = /^([a-zA-Z0-9]+[a-zA-Z0-9._%\-]*@(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,4})$/;
	if (!emailField.value.match(regexp)) {
		// emailField.focus();
		$('email_alreadyTaken').hide();
		$('invalid_email_address').show();
		$('emails_problem_img').show();
		$('emails_OK_img').hide();
		return false;
	}


	// check if the email isn't already taken by someone else
	var url = "/vcctl/admin/register.do?action=check_email&email="+encodeURIComponent(emailField.value);
	new Ajax.Request(url, {
		method: 'post',
		onSuccess: function(transport) {
			if (transport.responseText == "email_alreadyTaken") {
				$('email_alreadyTaken').show();
				$('invalid_name').hide();
				$('badSize_name').hide();
				$('emails_problem_img').show();
				$('emails_OK_img').hide();
				return false;
			}
		}
	});

	$('email_alreadyTaken').hide();
	$('invalid_email_address').hide();
	$('emails_problem_img').hide();
	$('emails_OK_img').hide();
	*/
        return true;
}

function checkEmails() {
        /**
        * Disabling this function for now
        */
        /*	
        if (!checkEmailValidity($('confirmEmail'))) {
		return false;
	}
	if (document.forms[0].email.value != document.forms[0].confirmEmail.value) {
		// $('confirmEmail').focus();
		$('email_adresses_dontMatch').show();
		$('emails_problem_img').show();
		$('emails_OK_img').hide();
		return false;
	}
	$('email_adresses_dontMatch').hide();
	$('emails_problem_img').hide();
	$('emails_OK_img').show();
	*/
        return true;
}

function checkPasswords() {
	var password = document.forms[0].password.value;
	var confirmPassword = document.forms[0].confirmPasword.value;
	if (password.length === 0) {
		// document.forms[0].password.focus();
		$('passwords_empty').show();
		$('passwords_dontMatch').hide();
		$('passwords_problem_img').show();
		$('passwords_OK_img').hide();
		return false;
	}
	if (password != confirmPassword) {
		// $('confirmPasword').focus();
		$('passwords_dontMatch').show();
		$('passwords_empty').hide();
		$('passwords_problem_img').show();
		$('passwords_OK_img').hide();
		return false;
	}
	$('passwords_dontMatch').hide();
	$('passwords_empty').hide();
	$('passwords_problem_img').hide();
	$('passwords_OK_img').show();
	return true;
}

function checkUserName(theField) {
	var name = theField.value;
	var url = "/vcctl/admin/register.do?action=check_username&userName="+encodeURIComponent(name);
	checkName(name, url);
}

function checkUserInfo() {
	return (checkEmails() && checkPasswords() && checkUserName(document.forms[0].userName));
}


/**
* Mix functions
**/

function checkMixName(theField) {
	var name = theField.value;
	var url = "/vcctl/operation/prepareMix.do?action=check_mix_name&mix_name="+encodeURIComponent(name);
	checkName(name, url);
}


/**
* Hydration functions
**/

function checkHydrationName(theField) {
	var name = theField.value;
	var url = "/vcctl/operation/hydrateMix.do?action=check_hydration_name&operation_name="+encodeURIComponent(name);
	checkName(name, url);
}


/**
* Common functions
**/

/**
* Check if the name is valid by doing some verifications,
* including asking to the server if the name isn't already taken.
* @param name the name
* @param url the Struts action for asking to the server if the name isn't already taken
**/
function checkName(name, url) {
	$('invalid_name').hide();
	$('badSize_name').hide();
	$('name_alreadyTaken').hide();
	$('name_problem_img').hide();
	$('name_OK_img').hide();

	if (name.length > 64 || name.length < 3) {
		$('badSize_name').show();
		$('name_problem_img').show();
		return false;
	}

	if (!checkNameValidity(name)) {
		$('invalid_name').show();
		$('name_problem_img').show();
		return false;
	}

	// check if the name isn't already taken
	new Ajax.Request(url, {
		method: 'post',
		onSuccess: function(transport) {
			if (transport.responseText == "name_alreadyTaken") {
				$('invalid_name').hide();
				$('badSize_name').hide();
				$('name_OK_img').hide();
				$('name_alreadyTaken').show();
				$('name_problem_img').show();
				return false;
			}
		}
	});

	$('name_OK_img').show();
	return true;
}

/**
* Check if the name is valid.
* The name must NOT:
* 	- begin by a dot
* 	- contain any of the following characters: * " / \ [ ] : ; | = ? % < > \t \n \r 
* 	- be equal to one of those names (or one of those names followed by an extension):"CON","PRN","AUX","NUL","COM1","COM2","COM3","COM4","COM5","COM6",
* "COM7","COM8","COM9","LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9","CLOCK$","null"
**/
function checkNameValidity(name) {
	var regexp = /^[^\.\*\"\/\\\[\]:;|=\?%<>\t\n\r][^\*\"\/\\\[\]:;|=\?%<>\t\n\r]+$/;
	if (!name.match(regexp)) {
		return false;
	}

	var forbiddenNames = ["CON","PRN","AUX","NUL","COM1","COM2","COM3","COM4","COM5","COM6",
	"COM7","COM8","COM9","LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9","CLOCK$","null"];

	for (var i = 0; i < forbiddenNames.length; i++) {
		// forbid the names described in forbiddenNames and those names with an extension
		regexp = new RegExp("^" + forbiddenNames[i] + "(\\..*)*$");
		if (name.match(regexp)) {
			return false;
		}
	}
	return true;
}