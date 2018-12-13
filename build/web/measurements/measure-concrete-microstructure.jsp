<!-- measure-concrete-microstructure JSP -->

<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>
<%@taglib uri="http://struts.apache.org/tags-nested" prefix="nested" %>

<script type="text/javascript">
    selectTab(3);
    if (!$$('#subtabs-right ul')[0] || !$$('#subtabs-right ul')[0].hasChildNodes() || ($$('#subtabs-right ul li')[0] && $$('#subtabs-right ul li')[0].id != "cement-materials")) {
        var titles = new Array();
        titles[0] = "Plot Hydrated Properties";
        titles[1] = "Measure Cement/Concrete Properties";
        var ids = new Array();
        ids[0] = "measure-hydrated-mix";
        ids[1] = "measure-concrete-microstructure";
        var urls = new Array();
        urls[0] = "<%=request.getContextPath()%>/measurements/initializeHydratedMixMeasurements.do";
        urls[1] = "<%=request.getContextPath()%>/measurements/initializeConcreteMeasurements.do";
        createSubTabsMenu(titles,ids,urls);
    }
    $('subtab-menu').show();
    $('top-border').hide();
    selectSubTab(1);
</script>

<html:xhtml />

<h3>Measure Cement or Concrete Properties</h3><span id="measure-hydrated-mix-overview" class="help-icon"></span>
<h3> </h3>
<br>
<html:form action="/measurements/measureConcreteMicrostructure.do">
    <br>
    <div id="hydrationName" class="to-reload">
        <table cellpadding="30">
            <tr>
                <th width="250">Choose the hydration result:</th>
                <td>
        <html:select property="hydrationName" onchange="ajaxUpdateContainerWithStrutsAction('/vcctl/measurements/measureConcreteMicrostructure.do?action=change_mix',this.form,'content')">
            <html:options property="userFinishedHydratedMixList" />
        </html:select><span id="measure-hydrated-mix-choosemix" class="help-icon"></span>
                </td>
            </tr>
        </table>
        </div>
    <br>
    <logic:messagesNotPresent property="no-results">
        <bean:size id="hydratedImagesNumber" name="concreteMeasurementsForm" property="hydratedImagesList" />
        <logic:greaterThan name="hydratedImagesNumber" value="0">
                <legend><b>Properties</b></a><span id="measure-hydrated-mix-properties" class="help-icon"></span></legend>
                <div>
                    <nested:iterate name="concreteMeasurementsForm" property="hydratedImagesList" indexId="ind">
                        <fieldset id="property-measurement_<%=ind%>" class="collapsed">
                            <legend class="collapsable-title collapsed"><a onclick="collapseExpand('property-measurement_<%=ind%>');"><b>After <nested:write property="measurementTime"/> hours hydration</b></a></legend>
                            <nested:define id="measurementTime" property="measurementTime" />
                            <div class="collapsable-content collapsed">
                                <div class="property-heading">Elastic Properties</div>
                                <nested:notEmpty property="effectiveModuliFileContent">
                                    <div id="effective_moduli_<%=ind%>" class="file-text-area"><nested:write property="effectiveModuliFileContent" filter="false"/></div>
                                </nested:notEmpty>
                                <nested:notEmpty property="phaseContributionsFileContent">
                                    <div id="phase-contributions_<%=ind%>" class="file-text-area"><nested:write property="phaseContributionsFileContent" filter="false"/></div>
                                </nested:notEmpty>
                                <nested:notEmpty property="ITZModuliFileContent">
                                    <div id="itz-moduli_<%=ind%>" class="file-text-area"><nested:write property="ITZModuliFileContent" filter="false"/></div>
                                </nested:notEmpty>
                                <input type="button" name="measure_elastic_moduli_<%=ind%>" onclick="ajaxUpdateContainerWithStrutsAction('/vcctl/measurements/measureConcreteMicrostructure.do?action=measure_elastic_moduli&time=<%=measurementTime%>',this.form,'elastic-moduli-measurement');" value="Measure Elastic Moduli" />
                                <div class="property-heading">Transport Properties</div>
                                <nested:notEmpty property="transportFactorFileContent">
                                    <div id="transport-factor_<%=ind%>" class="file-text-area"><nested:write property="transportFactorFileContent" filter="false"/></div>
                                </nested:notEmpty>
                                <nested:notEmpty property="transportPhaseContributionsFileContent">
                                    <div id="transport-factor_<%=ind%>" class="file-text-area"><nested:write property="transportPhaseContributionsFileContent" filter="false"/></div>
                                </nested:notEmpty>
                                <nested:notEmpty property="transportITZFileContent">
                                    <div id="transport-factor_<%=ind%>" class="file-text-area"><nested:write property="transportITZFileContent" filter="false"/></div>
                                </nested:notEmpty>
                                <input type="button" name="measure_transport_factor_<%=ind%>" onclick="ajaxUpdateContainerWithStrutsAction('/vcctl/measurements/measureConcreteMicrostructure.do?action=measure_transport_factor&time=<%=measurementTime%>',this.form,'transport-factor-measurement');" value="Measure Transport Factor" />
                            </div>
                        </fieldset>
                    </nested:iterate>
                </div>
            </fieldset>
        </logic:greaterThan>
    </logic:messagesNotPresent>
    <logic:messagesPresent property="no-results">
		There are no results for this hydrated mix.
    </logic:messagesPresent>
</html:form>
<!-- Tooltip Help -->
<div id="measure-hydrated-mix-overview_tt" class="tooltip" style="display:none">
    <p>Just like in a physical lab, virtual measurements can be made on virtual materials.  These
        measurements divide into two categories:  (1) <b>Continuous</b> measurements that are made as the
        material hydrates.  This includes heat release, degree of hydration, chemical shrinkage,
        pore solution pH, gel-space ratio, and many others.  (2) <b>Periodic</b> measurements,
        which can be made at specific intervals, such as linear elastic constants, compressive strength,
        and effective conductivity.</p>
    <p>Continuous measurements can be viewed in the Plotting section on this page.
        Any quantity can be plotted on the y-axis in terms of its relation to any other quantity on
        the x-axis.  Periodic measurements can be made by going to the relevant section on this
        page (e.g., Elastic moduli) and clicking on the "Measure" button for the time of interest.</p>
</div>

<div id="measure-hydrated-mix-choosemix_tt" class="tooltip" style="display:none">
    <p>Any hydrated mix should be available from the pull-down menu.  Choose a mix and then
        proceed with measurements.</p>
</div>

<div id="measure-hydrated-mix-properties_tt" class='tooltip' style="display:none">
    <p>In this section, measurements can be made at any of the times that were specified for output of
        the hydrated microstructure on the <b>Hydrate Mix</b> page.  Clicking on the "Measure" button at any time will
        cause the measurement to be made.  Once the measurement has been completed, text windows will appear
        above the "Measure" button showing the results of the measurement.  Once a measurement has been made
        at a given time, the text windows will always display the result, so it is easy to determine which
        measurements have been made.</p>
    <p><b>New in Version 8.0</b>: If elastic properties are measured for a mortar or concrete, then the
        predicted mortar/concrete elastic moduli and compressive strength are displayed, in addition to the
        elastic propertiesof the paste, when the calculation is finished.</p>
    <p><b>New in Version 8.0</b>: Measurements can now be made of the relative diffusion coefficient of a
        cement paste, also called the transport factor, and defined as the apparent diffusion coefficient of the paste
        divided by the diffusion coefficient in the bulk pore solution.</p>
</div>

<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("measure-hydrated-mix-overview", "measure-hydrated-mix-overview_tt");
    Tooltip.add("measure-hydrated-mix-choosemix", "measure-hydrated-mix-choosemix_tt");
    Tooltip.add("measure-hydrated-mix-properties", "measure-hydrated-mix-properties_tt");
</script>