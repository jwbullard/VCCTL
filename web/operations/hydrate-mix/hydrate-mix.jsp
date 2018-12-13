<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>

<html:xhtml />
<div>
<script type="text/javascript">
<!--
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
		createSubTabsMenu(titles,ids,urls,ids[1]);
	}
	$('subtab-menu').show();
	$('top-border').hide();
	selectSubTab(1);
	//-->
</script>

<h3>Step 2: Hydrate my mix</h3><span id="hydrate-mix-overview" class="help-icon"></span>

<html:form action="/operation/hydrateMix.do" onsubmit="createHydration(documents.forms[0]);">
	<fieldset>
		<legend><b>Mix properties</b><span id="hydrate-mix-properties" class="help-icon"></span></legend>
		<tiles:insert attribute="mix-properties" />
	</fieldset>
	<fieldset>
		<legend><b>Curing conditions</b> <span id="hydrate-mix-curing" class="help-icon"></span></legend>
		<tiles:insert attribute="curing-conditions" />
	</fieldset>
	<fieldset class="hidden">
		<legend><b>Cracking</b></legend>
	</fieldset>
	<fieldset id="simulation-parameters" class="collapsed">
		<legend class="collapsable-title collapsed"><a onclick="collapseExpand('simulation-parameters');"><b>Simulation parameters</b></a><span id="hydrate-mix-simulation-parameters" class="help-icon"></span></legend>
		<div class="collapsable-content collapsed">
			<tiles:insert attribute="hydration-simulation-parameters" />
		</div>
	</fieldset>
	<fieldset id="data-output" class="collapsed">
		<legend class="collapsable-title collapsed"><a onclick="collapseExpand('data-output');"><b>Data output</b></a> <span id="hydrate-mix-output" class="help-icon"></span></legend>
		<div class="collapsable-content collapsed">
			<tiles:insert attribute="data-output" />
		</div>
	</fieldset>
	<div class="problem_msg" id="name_alreadyTaken" style="display:none">
		You already have an hydration with the same name.
	</div>
	<div class="problem_msg" id="invalid_name" style="display:none">
		The hydration name is not valid. Try to use another name, with no punctuation marks. Some names are reserved and can not be used, too.
	</div>
	<div class="problem_msg" id="badSize_name" style="display:none">
		The hydration name must be between 3 and 64 characters.
	</div>
	<div id="operation_name" class="to-reload item_name">
		File name:
		<html:text property="operation_name" size="24" onblur="checkHydrationName(this);"/>
		<logic:messagesPresent property="alreadyused">
			<html:errors property="alreadyused" />
		</logic:messagesPresent>
		<img id="name_OK_img" src="<%=request.getContextPath()%>/images/ok.gif" alt="" style="display:none" />
		<img id="name_problem_img" src="<%=request.getContextPath()%>/images/problem.gif" alt="" style="display:none" />
	</div>
	<div id="submit-button">
		<input type="button" name="submit" value="Hydrate the mix" onclick="createHydration(this.form);" />
	</div>
</html:form>

<%-- Tool tips --%>

<div class="tooltip" style="display:none" id="hydrate-mix-overview_tt" >
    <p>In this space you can specify the material characteristics of the mix you wish
    to hydrate.  First, <b>Choose a mix</b> by selecting a previously made mix from the
    pulldown menu.  Next, review or change the apparent <b>activation energies</b> for the various
    kinds of reactions that can occur.  If interested in the effects of admixtures on hydration
    and microstructure, you may simulate the addition of an admixture
that deactivates all or part of the surface of any phase in the mix by modifying the
    <b>Surface deactivation</b> parameters.  Finally, you may shorten the induction period, alter the
    microstructure, and stimulate early-age hydration by adding CSH nucleation seeds to the mix water.</p>
</div>

<div class="tooltip" style="display:none" id="hydrate-mix-properties_tt" >
    <p>In this space you can specify the material characteristics of the mix you wish
    to hydrate.  First, <b>Choose a mix</b> by selecting a previously made mix from the
    pulldown menu.  Next, review or change the apparent <b>activation energies</b> for the various
    kinds of reactions that can occur.  Finally, you may simulate the addition of an admixture
that deactivates all or part of the surface of any phase in the mix by modifying the
    <b>Surface deactivation</b> parameters.</p>
</div>

<div class="tooltip" style="display:none" id="csh_seeds_tt" >
    <p>Small seed particles of C-S-H gel can be added to the mix water to stimulate
    growth of C-S-H.  All C-S-H seed particles are assumed to have an effective
    diameter of 1 micrometer.</p>
    <p>The value entered in the box is the number of seed particles per cubic
     micrometer of solution.  Therefore, values must be in the range [0,1].
     Note, however, that every seed particle occupies volume that otherwise would
     be occupied by the same volume of water, so a value of 1 seed/cubic micrometer
     corresponds to no solution at all.  In fact, values greater than 0.5 are likely
     to produce unusual or unphysical results due to lack of water in the system.
</div>

<div class="tooltip" style="display:none" id="hydrate-mix-curing_tt" >
    <p>This section contains options for setting the thermal and moisture conditions
        for hydration.  You may choose either isothermal, adiabatic, or semi-adiabatic <b>thermal</b>
        conditions.
If you choose isothermal, then the only other condition you can specify is the temperature.
If you choose semi-adiabatic, then you must also choose values for the ambient temperature and
the overall heat transfer coefficient between specimen and surroundings.  Additionally, if
your mix contains aggregate, you will see options for settng the initial aggregate temperature
and the heat transfer coefficient between aggregate and binder.</p>
</div>

<div class="tooltip" style="display:none" id="saturation_conditions_tt" >
    <p>For the <b>saturation</b> conditions, you may choose either saturated or sealed conditions.</p> 
</div>

<div class="tooltip" style="display:none" id="hydrate-mix-aging_tt" >
    <p>This section allows you to specify the duration of your hydration run.  You may choose
to specify the age (in days) to terminate hydration, or you may specify a maximum degree of
hydration at which to stop.  If you specify the age, then you also should review and possibly
modify the time conversion factor.  The value of 3.5e-4 that is displayed seems to be a good
default value for a number of cements and curing conditions.</p> 
</div>

<div class="tooltip" style="display:none" id="hydrate-mix-simulation-parameters_tt" >
    <p>If you expand this section, you will be able to modify the default parameter file or
the random number generator seed.  Usually there is no need to change either of these.</p> 
</div>

<div class="tooltip" style="display:none" id="hydrate-mix-output_tt" >
    <p>This section allows you to tailor the frequency at which some kinds of data are output
during a simulation.  In VCCTL 7.0, you specify these frequencies in terms of time rather than
cycles.  Note the units that are required for each field.</p> 
</div>

<!-- End of Tooltip Help -->
<script type="text/javascript">
<!--
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("hydrate-mix-overview", "hydrate-mix-overview_tt");
    Tooltip.add("hydrate-mix-properties", "hydrate-mix-properties_tt");
    Tooltip.add("csh_seeds", "csh_seeds_tt");
    Tooltip.add("hydrate-mix-curing", "hydrate-mix-curing_tt");
    Tooltip.add("hydrate-mix-aging", "hydrate-mix-aging_tt");
    Tooltip.add("hydrate-mix-simulation-parameters", "hydrate-mix-simulation-parameters_tt");
    Tooltip.add("hydrate-mix-output", "hydrate-mix-output_tt");
    Tooltip.add("hydrate-mix-saturation-conditions", "saturation_conditions_tt");
//-->
</script>
</div>