<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>
<%@page import="nist.bfrl.vcctl.database.*" %>
<%@page import="java.util.*" %>

<html:xhtml />
<script type="text/javascript">
	selectTab(2);
	if (!$$('#subtabs-right ul')[0] || !$$('#subtabs-right ul')[0].hasChildNodes() || ($$('#subtabs-right ul li')[0] && $$('#subtabs-right ul li')[0].id != "prepare-mix")) {
		var titles = new Array();
		titles[0] = "1. Prepare Mix";
		titles[1] = "2. Hydrate Mix";
		var ids = new Array();
		ids[0] = "prepare-mix";
		ids[1] = "hydrate-mix";
		var urls = new Array();
		urls[0] = "<%=request.getContextPath()%>/operation/initializeMix.do";
		urls[1] = "<%=request.getContextPath()%>/operation/initializeHydration.do";
		createSubTabsMenu(titles,ids,urls);
	}
	$('subtab-menu').show();
	$('top-border').hide();
	selectSubTab(0);
</script>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<h3>Step 1: Prepare mix</h3><span id="prepare-mix-overview" class="help-icon"></span>
<html:form action="/operation/prepareMix.do" onsubmit="createMix(documents.forms[0]);">
    <fieldset>
        <legend><b>Binder</b><span id="prepare-mix-binder" class="help-icon"></span></legend>
        <span id="psds" class="block-displayed">Choose a cement: 
            <html:select property="cementName" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_cement',this.form)" >
                <html:options name="cement_database" property="cements" />
            </html:select>
        </span>
        <div id="phase-distribution" class="collapsable-element">
            <div id="phase-distribution-title" class="collapsable-title collapsed"><a onclick="collapseExpand('phase-distribution');">Modify phase distribution in the <em>clinker</em></a></div>
            <div id="phase-distribution-content" class="collapsable-content collapsed">
                <tiles:insert attribute="phase-distribution" />
            </div>
        </div>
        <div id="calcium-sulfate-amounts" class="collapsable-element">
            <div id="calcium-sulfate-amounts-title" class="collapsable-title collapsed"><a onclick="collapseExpand('calcium-sulfate-amounts');">Modify calcium sulfate amounts in the <em>cement</em></a></div>
            <div id="calcium-sulfate-amounts-content" class="collapsable-content collapsed">
                <tiles:insert attribute="calcium-sulfate-amounts" />
            </div>
        </div>
        <div id="add-SCM" class="collapsable-element">
            <div id="add-SCM-title" class="collapsable-title collapsed"><a onclick="collapseExpand('add-SCM');">Add SCM or filler to the <em>binder</em></a><span id="prepare-mix-new-scm-feature" class="help-icon"></span></div>
            <div id="add-SCM-content" class="collapsable-content collapsed">
                <tiles:insert attribute="add-SCM" />
            </div>
        </div>
    </fieldset>
    <fieldset>
        <legend><b>Mix</b><span id="prepare-mix-mix" class="help-icon"></span></legend>
        <tiles:insert attribute="mixing-proportions" />
    </fieldset>
    <fieldset id="microstructure-simulation-parameters" class="collapsed">
        <legend class="collapsable-title collapsed"><a onclick="collapseExpand('microstructure-simulation-parameters');"><b>Simulation parameters</b></a><span id="prepare-mix-simulation-parameters" class="help-icon"></span></legend>
        <div class="collapsable-content collapsed">
            <tiles:insert attribute="microstructure-simulation-parameters" />
        </div>
    </fieldset>
    <div class="problem_msg" id="name_alreadyTaken" style="display:none">
        You already have a mix with the same name.
    </div>
    <div class="problem_msg" id="invalid_name" style="display:none">
        The mix name is not valid. Try to use another name, with no punctuation marks. Some names are reserved and can not be used, too.
    </div>
    <div class="problem_msg" id="badSize_name" style="display:none">
        The mix name must be between 3 and 64 characters.
    </div>
    <span class="item_name">
        File name: <html:text property="mix_name" size="16" onblur="checkMixName(this);"/>
		<span id="prepare-mix-name" class="help-icon"></span>
    </span>
    <img id="name_OK_img" src="<%=request.getContextPath()%>/images/ok.gif" alt="" style="display:none" />
    <img id="name_problem_img" src="<%=request.getContextPath()%>/images/problem.gif" alt="" style="display:none" />
    <span id="comments">
        Notes: <html:textarea property="notes" cols="40" rows="5" styleClass="notes"/>
		<span id="prepare-mix-notes" class="help-icon"></span>
    </span>
    <div id="submit-button">
        <input type="button" name="submit" value="Create the mix" onclick="createMix(this.form);" />
    </div>
</html:form>

<!-- Tooltip Help -->
<div id="prepare-mix-overview_tt" class="tooltip" style="display:none">
    <p>This is a one-stop form to prepare any kind of mix:  cement paste, mortar, or concrete. The binder solids information is specified in the top block, <b>Binder</b>. Overall mix proportioning (w/s ratio, fractions of binder, aggregate, etc.) is entered in the <b>Mix</b>. For finer tuning of the simulation, expand the <b>Simulation parameters</b> block.</p>
	<p>Enter a name for your mix, and type any notes to yourself that you want to be recorded for future reference.</p>
</div>

<div id="prepare-mix-binder_tt" class="tooltip" style="display:none">
    <p>This section is used to specify cement binder composition and particle size distribution. You specify the base-line properties of the binder by selecting a cement from the drop-down menu (<b>Choose a cement</b>). This will specify the clinker particle size distribution (PSD), and also will fill in default values for clinker composition and calcium sulfate carriers.</p>
    <p>To change the clinker composition, simply expand the section called <b>Modify phase distribution...</b> and fill in the desired values for volume fraction and surface area fraction of the various components. The default values come from the cement you chose in the drop-down menu.</p>
    <p>You can also modify the PSDs and amounts of calcium sulfate carriers in the cement by expanding the section called <b>Modify calcium sulfate...</b>. Select from the drop-down menu next to each sulfate phase to change its PSD, and enter either the mass fraction or volume fraction, on a CEMENT SOLIDS BASIS.</p>
    <p>Finally, you can replace a portion of the cement with a supplementary cementitious material (SCM) by expanding the <b>Add SCM...</b> section. In this section you can choose any combination of SCMs by checking the box next to their names. The PSD of each SCM can be customized by selecting a PSD from the drop-down menu, and you can specify the fraction replacement either as volume fraction or mass fraction.</p>
</div>

<div id="prepare-mix-new-scm-feature_tt" class="tooltip" style="display:none">
    <p><b>New in Version 8.0</b>: Fly ash and silica fume are always added as spherical particles, even if you choose to use real shape cement particles</p>
</div>

<div id="prepare-mix-mix_tt" class='tooltip' style="display:none">
    <p>This section is used to specify the global proportions of the specimen. To make a cement paste, just type in the desired <b>Water/Binder ratio</b> (mass basis). This will automatically set the mass fractions of solid and water.</p>
    <p>To create a mortar, simply type in the <b>Water/Binder ratio</b> (mass basis), and then check the box next to <b>Add Fine Aggregate</b>. This causes a new section to appear, in which you specify the properties of your aggregate. Selecting the <b>Aggregate Source</b> from the drop-down menu will dial in its shape characteristics and elastic moduli. The value of specific gravity defaults to the value for the selected aggregate source, but you can change it if you like. Finally, you can specify the aggregate grading in the table, or select a grading from the drop-down menu. You can even save a customized grading for later use.</p>
    <p> The steps for creating a concrete are exactly like those for a mortar, except you also check the box next to <b>Add Coarse Aggregate</b> and follow the same procedure as you do for fine aggregate</p>
    <p>For a mortar or concrete, you must specify the mass (or volume) fraction of fine and/or coarse aggregate in the boxes next to <b>Add Fine Aggregate</b>
        and <b>Add Coarse Aggregate</b>, respectively. Also, you should fill in a value for the entrained air content at the bottom of the section (default value is 0.04. Entrained air simply increases the total volume of the mix; it does not affect the mix proportions you specified in any way.</p>
</div>
<div id="prepare-mix-simulation-parameters_tt" class='tooltip' style="display:none">
    <p>This section contains information about parameters that change the way the virtual mix is assembled. You can choose your own <b>random number generator seed</b> by entering <i>negative</i> integer in the box. You may want to do this if you want to ensure that multiple simulations all sample random numbers in exactly the same sequence. Otherwise, you can ignore this field.</p>
    <p>You can choose the shape characteristics of the binder particles by checking the box next to <b>Use real particle shapes...</b> and then selecting the shape set from the drop-down menu</p>
    <p>Cement particles can be forced to form agglomerates by checking the <b>Flocculation</b>
    box and entering the desired degree of flocculation, between 0 and 1. Note: larger values mean more flocculation</b>
    <p>To simulate the influence of a superplasticizer, you can force all cement particles to be separated by a distance of 1 or 2 micrometers, by checking the <b>Dispersion</b> box. Note: Dispersion and flocculation cannot be chosen simulataneously.</p>
    <p>The default system size for cement paste is a cube 100 micrometers on a side, but you can change the dimensions to any you like. Note that larger dimensions will take longer to create and hydrate. If you are making a virtual mortar or concrete, then you also can choose the dimensions and resolution of the larger-scale concrete structure that will be created.</b>
</div>

<div id="prepare-mix-name_tt" class='tooltip' style="display:none">
    <p>You must give a name to your specimen, whether it is a cement, mortar or concrete. The name must not be the same as any other specimen you have made previously. A green checkmark will appear if the name you give is okay.</p>
</div>

<div id="prepare-mix-notes_tt" class='tooltip' style="display:none">
    <p>You may optionally type any text in the <b>Notes</b> box. The text you enter will be stored with the virtual specimen and can be viewed later.</p>
</div>

<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("prepare-mix-overview", "prepare-mix-overview_tt");
    Tooltip.add("prepare-mix-binder", "prepare-mix-binder_tt");
    Tooltip.add("prepare-mix-new-scm-feature", "prepare-mix-new-scm-feature_tt");
    Tooltip.add("prepare-mix-mix", "prepare-mix-mix_tt");
    Tooltip.add("prepare-mix-simulation-parameters", "prepare-mix-simulation-parameters_tt");
    Tooltip.add("prepare-mix-name", "prepare-mix-name_tt");
    Tooltip.add("prepare-mix-notes", "prepare-mix-notes_tt");
</script>