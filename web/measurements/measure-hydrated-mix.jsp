<%-- measure-hydrated-mix JSP --%>

<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>
<%@taglib uri="http://struts.apache.org/tags-nested" prefix="nested" %>

<html:xhtml />
<script type="text/javascript">
    selectTab(3);
    if (!$$('#subtabs-right ul')[0] || !$$('#subtabs-right ul')[0].hasChildNodes() || ($$('#subtabs-right ul li')[0] && $$('#subtabs-right ul li')[0].id != "measure-hydrated-mix")) {
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
    selectSubTab(0);
</script>


<h3>Plot Properties of Hydrated Cement Paste</h3><span id="measure-hydrated-mix-overview" class="help-icon"></span>
<html:form action="/measurements/measureHydratedMix.do">
    <div id="chart-values" class="to-reload">
        <logic:present name="chart">
            <input type="hidden" value="${chart.XMin}" name="xMin"/>
            <input type="hidden" value="${chart.XMax}" name="xMax"/>
            <input type="hidden" value="${chart.YMin}" name="yMin"/>
            <input type="hidden" value="${chart.YMax}" name="yMax"/>
            <input tYpe="hidden" value="${chart.XMinValue}" name="xMinValue"/>
            <input type="hidden" value="${chart.XMaxValue}" name="xMaxValue"/>
            <input type="hidden" value="${chart.YMinValue}" name="yMinValue"/>
            <input type="hidden" value="${chart.YMaxValue}" name="yMaxValue"/>
        </logic:present>
    </div>
    <br>
    <logic:messagesNotPresent property="no-results">
        <fieldset>
		<legend><b>Set axes</b></legend>
        <div id="XAxis" class="to-reload">
            <table>
                <tr>
                    <td width="50" height="30">
				    x-axis:
                    </td><td width="200" height="30">
                    <html:select property="XAxis" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/measurements/measureHydratedMix.do?action=change_plotting_element',this.form,'to-reload');">
                        <html:options property="XLabels" />
                    </html:select>
                    </td>
                </tr>
            </table>
        </div>
        <br>
        <div id="yPlottingElements-group" class="to-reload">
            <div class="heading-labels">
                <table cellpadding="30">
                    <tr>
                        <td width="200" align="left">Hydration Name<span id="measure-hydrated-mix-choosemix" class="help-icon"></span></td>
                        <td width="200" align="left">Property</td>
                    </tr>
                </table>
            </div>
            <br>
            <div class="axis-labels">
                <table cellpadding="30">
                    <logic:iterate name="hydratedMixMeasurementsForm" property="YPlottingElements" id="YPlottingElement" indexId="ind">
                        <tr>
                            <bean:size id="yPlottingElementsNumber" name="hydratedMixMeasurementsForm" property="YPlottingElements" />
                        <div id="YPlottingElement_<%=ind%>" class="to-reload YPlottingElement">
                            <td width="200" align="left">
                                <html:select name="YPlottingElement" property="hydrationName" onchange="ajaxUpdateContainerWithStrutsAction('/vcctl/measurements/measureHydratedMix.do?action=change_mix',this.form,'to-reload');" indexed="true">
                                    <html:options property="userFinishedHydratedMixList" />
                                </html:select>
                            </td><td width="200" align="left">
                                <html:select name="YPlottingElement" property="hydrationProperty" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/measurements/measureHydratedMix.do?action=change_plotting_element',this.form,'to-reload');" indexed="true">
                                    <html:options property="YLabels" />
                                </html:select>
                            </td>
                        </div>
                        <td>
                            <% String plusStyle, minusStyle;
            if (yPlottingElementsNumber > 1) {%>
                            <input type = "button" name="remove_y_plotting_element_<%=ind%>" onclick="ajaxUpdateElementsWithStrutsAction('/vcctl/measurements/measureHydratedMix.do?action=remove_y_plotting_element&yPlottingElementToRemove=<%=ind%>',this.form,'to-reload');" value="-" />
                            <% }
            if (ind == (yPlottingElementsNumber - 1)) {%>
                            <input type="button" name="add_y_plotting_element_<%=ind%>" onclick="ajaxUpdateElementsWithStrutsAction('/vcctl/measurements/measureHydratedMix.do?action=add_y_plotting_element',this.form,'to-reload');" value="+" />
                            <% }%>
                        </td>
                        </tr>
                    </logic:iterate>
                </table>
            </div>
        </div>
        </fieldset>
        <fieldset>
            <legend><b>Plot result</b></legend>
        <br>
        <div id="result_graph" class="chart to-reload">
            <logic:present name="chart">
                <div id="selection-rect" onmouseup="onMouseUpOnSmallChart(event,this);" onmousemove="onMouseMoveOnSmallChart(event,this);">
                </div>
                <div id="result_graph_img" style="width: 512px; height: 384px; background: url(${chart.src}) no-repeat right;" onmousedown="onMouseDownOnChart(event,this);" onmouseup="onMouseUpOnSmallChart(event,this);" onmousemove="onMouseMoveOnSmallChart(event,this);" ondblclick="onDoubleClickOnSmallChart(event,this);">
                </div>
                <br>
                <a href="javascript:openInNewWindow('/vcctl/measurements/measureHydratedMix.do?action=display_big_chart');" class="link">High resolution version</a>
            </logic:present>
        </div>
        </fieldset>
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

<div id="measure-hydrated-mix-plotting_tt" class='tooltip' style="display:none">
    <p>In this section you can plot any continuously varying property of the microstructure in relation
        to any other quantity.  Choose the quantities for the x-axis and y-axis.  Multiple quantities can
        be plotted on the y-axis, as long as they are dimensionally commensurate with each other.  For
        example, degree of hydration and pore solution pH can both be plotted simultaneously because they
        are both dimensionless, but gel space ratio and heat release cannot be plotted simultaneously
        because gel space ratio is dimensionless while heat release has units of J/g solid.</p>
    <br><HR NOSHADE><br>
    <p><b>Zooming</b>. Any region of the visible plot can be examined in greater detail.  Click and drag
        the mouse from the beginning x value to the ending x value anywhere inside the plot, and a new plot
        will appear showing just that domain.  The y-axis will be automatically scaled to fill the plot
        region.</p>
</div>

<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("measure-hydrated-mix-overview", "measure-hydrated-mix-overview_tt");
    Tooltip.add("measure-hydrated-mix-choosemix", "measure-hydrated-mix-choosemix_tt");
    Tooltip.add("measure-hydrated-mix-plotting", "measure-hydrated-mix-plotting_tt");
</script>