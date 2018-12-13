<div id="tab-menu">
	<!-- Left corner of the tab menu -->
	<div id="tabs-left-corner"></div>

	<div id="tabs-right">
		<ul>
			<li id="home" class="current-left"><div class="current-right"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(0); new Ajax.Updater('content', '<%=request.getContextPath()%>/pages/home.jsp', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
			}
			});">Home</a></div></li>
			<li id="lab-materials" class="after-current"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(1); new Ajax.Updater('content', '<%=request.getContextPath()%>/lab-materials/initializeCementMaterials.do', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
                                $('subtab-menu').show();
			}, evalScripts:true});">Lab Materials</a></li>
                        <li id="mix"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(2); new Ajax.Updater('content', '<%=request.getContextPath()%>/operation/initializeMix.do', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
				$('subtab-menu').show();
				$('top-border').hide();
			}, evalScripts:true});">Mix</a></li>
			<li id="measurements"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(3); new Ajax.Updater('content', '<%=request.getContextPath()%>/measurements/initializeHydratedMixMeasurements.do', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
                                $('subtab-menu').show();
				$('top-border').hide();
			}, evalScripts:true});">Measurements</a></li>
			<li id="my-operations"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(4); new Ajax.Updater('content', '<%=request.getContextPath()%>/my-operations/initializeMyOperations.do', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
			}, evalScripts:true});">My Operations</a></li>
			<li id="my-files"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(5); new Ajax.Updater('content', '<%=request.getContextPath()%>/my-files/initializeMyMicrostructureFiles.do', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
			}, evalScripts:true});">My Files</a></li>
                        <li id="logout"><a onclick="$('subtab-menu').hide(); $('top-border').show(); $('preloader').show(); $('content').hide(); selectTab(6); new Ajax.Updater('content', '<%=request.getContextPath()%>/admin/initializeLogout.do', {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
			}, evalScripts:true});">Logout</a></li>
		</ul>
	</div>
</div>
