// select the tabIndex tab and deselect the previously selected

function selectTab(tabIndex)
{
	/**
	* 1. For the selected tab:
	* 	- set the class of the <li> element to "current-left"
	* 	- add a <div> child to <li> that will be the parent of the <a> element and set its class to "current-right"
	* 
	* 2. For the tab after the selected one:
	* 	- set the class of the <li> element to "after-current"
	* 
	* 3. For the first tab:
	* 	- set its class to "first-tab"
	**/

	// var previouslySelectedTab = ($('tabs-right').getElementsByClassName('current-left'))[0]; // the previously selected tab
	var previouslySelectedTab = ($('tabs-right').select('.current-left'))[0]; // the previously selected tab
	var newlySelectedTab = ($('tabs-right').down().immediateDescendants())[tabIndex]; // the newly selected tab

	if (newlySelectedTab.hasClassName('current-left') == false) { // change selected tab only if the user clicked on a different tab than the one that is selected

		var previouslySelectedTabChild = previouslySelectedTab.down().down(); // copy the <a> tag of the previously selected tab in order to insert it later
		previouslySelectedTab.down().remove(); // remove current_right div

		var newlySelectedTabChild = newlySelectedTab.down(); // copy the <a> tag of the newly selected tab in order to insert it later
		newlySelectedTabChild.remove(); // remove it

		// deselect the previously selected tab
		previouslySelectedTab.removeClassName('current-left');
		previouslySelectedTab.appendChild(previouslySelectedTabChild);

		// remove the 'after-current' class name from the first sibling of the previously selected tab
		if (previouslySelectedTab.next() != null) {
			previouslySelectedTab.next().removeClassName('after-current');
		}

		// make the newlySelectedTab tab the one wich is selected
		newlySelectedTab.className='current-left';
		var currentRightDiv = document.createElement('div');
		// currentRightDiv.addClassName('current-right'); // bug with Internet Explorer
		currentRightDiv.className = 'current-right';
		newlySelectedTab.appendChild(currentRightDiv);
		currentRightDiv.appendChild(newlySelectedTabChild); // copy  the <a> that was in home in current-right

		// mark the first tab as "first-tab" - used in the CSS file because IE doesn't support "first-child"
		var firstTab = $('tabs-right').down().down();
		if ((tabIndex > 0) && (firstTab.hasClassName('first-tab') == false)) {
			firstTab.className='first-tab';
		}

		// finally mark the first sibling of the newly selected tab as 'after-current'
		if (newlySelectedTab.next()) {
			newlySelectedTab.next().className='after-current';
		}
	}
}


function selectSubTab(tabIndex)
{
	// var previouslySelectedTab = ($('subtabs-right').getElementsByClassName('current-submenu'))[0]; // the previously selected tab
	var previouslySelectedTab = ($('subtabs-right').select('.current-submenu'))[0]; // the previously selected tab
	var newlySelectedTab = ($('subtabs-right').down().immediateDescendants())[tabIndex]; // the newly selected tab

	if (newlySelectedTab.hasClassName('current-submenu') == false) { // change selected tab only if the user clicked on a different tab than the one that is selected
		previouslySelectedTab.removeClassName('current-submenu');
		newlySelectedTab.addClassName('current-submenu');
	}
}

/**
* Create the submenu tabs, given their titles, ids and urls
* Selected the selectedTabID tab if specified, or the first one if not
**/
function createSubTabsMenu(titles, ids, urls, selectedTabID) {
	if (titles.length > 0 && titles.length == ids.length && ids.length == urls.length) {
		if (!$$('#subtabs-right ul')[0]) {
			$('subtabs-right').appendChild(document.createElement('ul'));
		}
		var subTabs = $$('#subtabs-right ul')[0];
		if (subTabs) {
			while (subTabs.hasChildNodes()) {
				subTabs.removeChild(subTabs.firstChild);
			}
			for (var i = 0; i < ids.length; i++) {
				var tab = document.createElement('li');
				tab.setAttribute('id',ids[i]);

				var link = document.createElement('a');
				var onClickScript = new Function("$('preloader').show(); $('content').hide(); selectSubTab(" + i + "); new Ajax.Updater('content', '" + urls[i] + "', {\n"
					+ "onComplete:function() {\n"
					+ "$('preloader').hide();\n"
					+ "$('content').show();\n"
					+ "}, evalScripts:true});");
				link.setAttribute('onclick',onClickScript);
				
				link.onclick = onClickScript;

				var title = document.createTextNode(titles[i]);

				link.appendChild(title);
				tab.appendChild(link);
				subTabs.appendChild(tab);
			}
			var selectedTab = $(selectedTabID);
			if (selectedTabID == null || selectedTab == null) {
				 selectedTab = $$('#subtabs-right ul')[0].firstChild;
			}
			if (selectedTab) {
				// selectedTab.addClassName('current-submenu'); // bug with Internet Explorer
				selectedTab.className = 'current-submenu';
			}
		}
	}
}