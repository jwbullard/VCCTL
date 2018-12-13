<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@page import="nist.bfrl.vcctl.operation.microstructure.*" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>

<%
            String[][] coarse01Grading = ((GenerateMicrostructureForm) session.getAttribute("mixingForm")).getCoarse01Grading();
            String[][] fine01Grading = ((GenerateMicrostructureForm) session.getAttribute("mixingForm")).getFine01Grading();
            String[][] coarse02Grading = ((GenerateMicrostructureForm) session.getAttribute("mixingForm")).getCoarse02Grading();
            String[][] fine02Grading = ((GenerateMicrostructureForm) session.getAttribute("mixingForm")).getFine02Grading();
%>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<table>
    <thead>
        <tr>
            <th></th>
            <th>Mass fraction</th>
            <th>Volume fraction</th>
        </tr>
    </thead>
    <tr>
        <td>Binder</td>
        <td>
            <span id="binder_massfrac"><html:text size="6" property="binder_massfrac" onchange="onChangeBinderMassFraction(this);" /></span>
        </td>
        <td>
            <span id="binder_volfrac"><html:text size="6" property="binder_volfrac" onchange="onChangeBinderVolumeFraction(this);" /></span>
        </td>
    </tr>
    <tr>
        <td>Water</td>
        <td>
            <span id="water_massfrac"><html:text size="6" property="water_massfrac" onchange="onChangeWaterMassFraction(this);" /></span>
        </td>
        <td>
            <span id="water_volfrac"><html:text size="6" property="water_volfrac" onchange="onChangeWaterVolumeFraction(this);" /></span>
        </td>
    </tr>
    <tr>
        <td>Water/Binder ratio</td>
        <td colspan="2">
            <span id="water_binder_ratio"><html:text size="6" property="water_binder_ratio" onchange="onChangeWaterBinderRatio(this);" /></span>
        </td>
    </tr>
    <tr>
        <td>
            <span id="add_coarse_aggregate01">
                <html:hidden property="add_coarse_aggregate01" />
                <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="true">
                    <input type="checkbox" name="add_coarse_aggregate01_checkbox" CHECKED onclick="addOrRemoveCoarseAggregate(this.form,'01');" /> Add Coarse Aggregate
                    </logic:equal>
                    <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="false">
                        <input type="checkbox" name="add_coarse_aggregate01_checkbox" onclick="addOrRemoveCoarseAggregate(this.form,'01');" /> Add Coarse Aggregate
                    </logic:equal>
            </span>
        </td>
        <td>
            <span id="coarse_aggregate01_massfrac">
                <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="true">
                    <html:text size="6" property="coarse_aggregate01_massfrac" onchange="onChangeAggregateMassFraction(this);" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="false">
                    <html:text size="6" property="coarse_aggregate01_massfrac" disabled="true" onchange="onChangeAggregateMassFraction(this);" />
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="coarse_aggregate01_volfrac">
                <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="true">
                    <html:text size="6" property="coarse_aggregate01_volfrac" onchange="onChangeAggregateVolumeFraction(this);" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="false">
                    <html:text size="6" property="coarse_aggregate01_volfrac" disabled="true" onchange="onChangeAggregateVolumeFraction(this);" />
                </logic:equal>
            </span>
        </td>
    </tr>
    <tr>
        <td colspan="3">
            <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="true">
                <div id="coarse_aggregate01_properties" class="collapsable-element">
                </logic:equal>
                <logic:equal name="mixingForm" property="add_coarse_aggregate01" value="false">
                    <div id="coarse_aggregate01_properties" class="collapsable-element hidden">
                    </logic:equal>
                    <div id="coarse_aggregate01_properties-title" class="collapsable-title collapsed"><a onclick="collapseExpand('coarse_aggregate01_properties');">Change properties</a>
                        <div id="coarse_aggregate01_properties-content" class="collapsable-content collapsed">
                            <span id="coarse_aggregate01_display_name" class="block-displayed">Aggregate source:
                                <html:select property="coarse_aggregate01_display_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_coarse_aggregate01',this.form);">
                                    <html:options name="cement_database" property="coarse_aggregates" />
                                </html:select>
                            </span>
                            <span id="coarse_aggregate01_sg" class="block-displayed">Specific gravity:
                                <html:text size="6" property="coarse_aggregate01_sg" onchange="updateMixVolumeFractions(this.form);" />
                            </span>
                            <span id="coarse_aggregate01_grading_name" class="block-displayed">Grading:
                                <html:select property="coarse_aggregate01_grading_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_coarse_aggregate01_grading',this.form)">
                                    <html:options name="cement_database" property="coarse_aggregate_gradings" />
                                </html:select>
                            </span>
                            <div>
                                <table>
                                    <tr>
                                        <th>Sieve</th>
                                        <th>Diameter (mm)</th>
                                        <th>Fraction Retained</th>
                                    </tr>
                                    <% for (int i = 0; i < coarse01Grading[0].length; i++) {%>
                                    <tr class="coarse_aggregate01_grading-line">
                                        <td>
                                            <span id="coarse_aggregate01_grading-sieve_name_<%=i%>"><%=coarse01Grading[0][i]%></span>
                                        </td>
                                        <td>
                                            <% if (i == 0) {%>
                                            <span id="coarse_aggregate01_grading-min_sieve_diameter_<%=i%>" class="coarse_aggregate01_grading-sieve_diameter"><%=coarse01Grading[1][i]%></span> - <span id="coarse_aggregate01_grading_max_diam"><html:text size="6" property="coarse_aggregate01_grading_max_diam"  onchange="checkCoarseAggregateGradingMaxDiam(this,'01');" /></span>
                                            <% } else {%>
                                            <span id="coarse_aggregate01_grading-min_sieve_diameter_<%=i%>" class="coarse_aggregate01_grading-sieve_diameter"><%=coarse01Grading[1][i]%></span> - <span id="coarse_aggregate01_grading-max_sieve_diameter_<%=i - 1%>"><%=coarse01Grading[1][i - 1]%></span>
                                            <% }%>
                                        </td>
                                        <td>
                                            <span id="coarse_aggregate01_grading_massfrac_<%=i%>" class="coarse_aggregate01_grading_massfrac"><input type="text" value="<%=coarse01Grading[2][i]%>" name="coarse_aggregate01_grading_massfrac_<%=i%>" onchange="onChangeCoarseAggregateGradingMassFrac(this,'01');" size="6"/></span>
                                        </td>
                                    </tr>
                                    <% }%>
                                    <tr>
                                        <td colspan="3">
                                            <hr />
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2">
									Total
                                        </td>
                                        <td>
                                            <span id="coarse_aggregate01_grading_total_massfrac"><input type="text" name="coarse_aggregate01_grading_total_massfrac" value="1.0" readonly="readonly" size="6"/></span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="3">
									Name:
                                            <span id="new_coarse_aggregate01_grading_name"><html:text size="15" property="new_coarse_aggregate01_grading_name" /></span>
                                            <input type="button" onclick="saveCoarseGrading(this.form,'01');" value="Save" />
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                    </td>
                    </tr>
                    <tr>
                    <tr>
                        <td>
                            <span id="add_coarse_aggregate02">
                                <html:hidden property="add_coarse_aggregate02" />
                                <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="true">
                                    <input type="checkbox" name="add_coarse_aggregate02_checkbox" CHECKED onclick="addOrRemoveCoarseAggregate(this.form,'02');" /> Add Coarse Aggregate 2
                                    </logic:equal>
                                    <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="false">
                                        <input type="checkbox" name="add_coarse_aggregate02_checkbox" onclick="addOrRemoveCoarseAggregate(this.form,'02');" /> Add Coarse Aggregate 2
                                    </logic:equal>
                            </span>
                        </td>
                        <td>
                            <span id="coarse_aggregate02_massfrac">
                                <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="true">
                                    <html:text size="6" property="coarse_aggregate02_massfrac" onchange="onChangeAggregateMassFraction(this);" />
                                </logic:equal>
                                <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="false">
                                    <html:text size="6" property="coarse_aggregate02_massfrac" disabled="true" onchange="onChangeAggregateMassFraction(this);" />
                                </logic:equal>
                            </span>
                        </td>
                        <td>
                            <span id="coarse_aggregate02_volfrac">
                                <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="true">
                                    <html:text size="6" property="coarse_aggregate02_volfrac" onchange="onChangeAggregateVolumeFraction(this);" />
                                </logic:equal>
                                <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="false">
                                    <html:text size="6" property="coarse_aggregate02_volfrac" disabled="true" onchange="onChangeAggregateVolumeFraction(this);" />
                                </logic:equal>
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3">
                            <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="true">
                                <div id="coarse_aggregate02_properties" class="collapsable-element">
                                </logic:equal>
                                <logic:equal name="mixingForm" property="add_coarse_aggregate02" value="false">
                                    <div id="coarse_aggregate02_properties" class="collapsable-element hidden">
                                    </logic:equal>
                                    <div id="coarse_aggregate02_properties-title" class="collapsable-title collapsed"><a onclick="collapseExpand('coarse_aggregate02_properties');">Change properties</a>
                                        <div id="coarse_aggregate02_properties-content" class="collapsable-content collapsed">
                                            <span id="coarse_aggregate02_display_name" class="block-displayed">Aggregate source:
                                                <html:select property="coarse_aggregate02_display_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_coarse_aggregate02',this.form);">
                                                    <html:options name="cement_database" property="coarse_aggregates" />
                                                </html:select>
                                            </span>
                                            <span id="coarse_aggregate02_sg" class="block-displayed">Specific gravity:
                                                <html:text size="6" property="coarse_aggregate02_sg" onchange="updateMixVolumeFractions(this.form);" />
                                            </span>
                                            <span id="coarse_aggregate02_grading_name" class="block-displayed">Grading:
                                                <html:select property="coarse_aggregate02_grading_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_coarse_aggregate02_grading',this.form)">
                                                    <html:options name="cement_database" property="coarse_aggregate_gradings" />
                                                </html:select>
                                            </span>
                                            <div>
                                                <table>
                                                    <tr>
                                                        <th>Sieve</th>
                                                        <th>Diameter (mm)</th>
                                                        <th>Fraction Retained</th>
                                                    </tr>
                                                    <% for (int i = 0; i < coarse02Grading[0].length; i++) {%>
                                                    <tr class="coarse_aggregate02_grading-line">
                                                        <td>
                                                            <span id="coarse_aggregate02_grading-sieve_name_<%=i%>"><%=coarse02Grading[0][i]%></span>
                                                        </td>
                                                        <td>
                                                            <% if (i == 0) {%>
                                                            <span id="coarse_aggregate02_grading-min_sieve_diameter_<%=i%>" class="coarse_aggregate02_grading-sieve_diameter"><%=coarse02Grading[1][i]%></span> - <span id="coarse_aggregate02_grading_max_diam"><html:text size="6" property="coarse_aggregate02_grading_max_diam"  onchange="checkCoarseAggregateGradingMaxDiam(this,'02');" /></span>
                                                            <% } else {%>
                                                            <span id="coarse_aggregate02_grading-min_sieve_diameter_<%=i%>" class="coarse_aggregate02_grading-sieve_diameter"><%=coarse02Grading[1][i]%></span> - <span id="coarse_aggregate02_grading-max_sieve_diameter_<%=i - 1%>"><%=coarse02Grading[1][i - 1]%></span>
                                                            <% }%>
                                                        </td>
                                                        <td>
                                                            <span id="coarse_aggregate02_grading_massfrac_<%=i%>" class="coarse_aggregate02_grading_massfrac"><input type="text" value="<%=coarse02Grading[2][i]%>" name="coarse_aggregate02_grading_massfrac_<%=i%>" onchange="onChangeCoarseAggregateGradingMassFrac(this,'02');" size="6"/></span>
                                                        </td>
                                                    </tr>
                                                    <% }%>
                                                    <tr>
                                                        <td colspan="3">
                                                            <hr />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td colspan="2">
									Total
                                                        </td>
                                                        <td>
                                                            <span id="coarse_aggregate02_grading_total_massfrac"><input type="text" name="coarse_aggregate02_grading_total_massfrac" value="1.0" readonly="readonly" size="6"/></span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td colspan="3">
									Name:
                                                            <span id="new_coarse_aggregate02_grading_name"><html:text size="15" property="new_coarse_aggregate02_grading_name" /></span>
                                                            <input type="button" onclick="saveCoarseGrading(this.form,'02');" value="Save" />
                                                        </td>
                                                    </tr>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                    </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <span id="add_fine_aggregate01">
                                                <html:hidden property="add_fine_aggregate01" />
                                                <logic:equal name="mixingForm" property="add_fine_aggregate01" value="true">
                                                    <input type="checkbox" name="add_fine_aggregate01_checkbox" CHECKED onclick="addOrRemoveFineAggregate(this.form,'01');" /> Add Fine Aggregate
                                                    </logic:equal>
                                                    <logic:equal name="mixingForm" property="add_fine_aggregate01" value="false">
                                                        <input type="checkbox" name="add_fine_aggregate01_checkbox" onclick="addOrRemoveFineAggregate(this.form,'01');" /> Add Fine Aggregate
                                                    </logic:equal>
                                            </span>
                                        </td>
                                        <td>
                                            <span id="fine_aggregate01_massfrac">
                                                <logic:equal name="mixingForm" property="add_fine_aggregate01" value="true">
                                                    <html:text size="6" property="fine_aggregate01_massfrac" onchange="onChangeAggregateMassFraction(this);" />
                                                </logic:equal>
                                                <logic:equal name="mixingForm" property="add_fine_aggregate01" value="false">
                                                    <html:text size="6" property="fine_aggregate01_massfrac" disabled="true" onchange="onChangeAggregateMassFraction(this);" />
                                                </logic:equal>
                                            </span>
                                        </td>
                                        <td>
                                            <span id="fine_aggregate01_volfrac">
                                                <logic:equal name="mixingForm" property="add_fine_aggregate01" value="true">
                                                    <html:text size="6" property="fine_aggregate01_volfrac" onchange="onChangeAggregateVolumeFraction(this);" />
                                                </logic:equal>
                                                <logic:equal name="mixingForm" property="add_fine_aggregate01" value="false">
                                                    <html:text size="6" property="fine_aggregate01_volfrac" disabled="true" onchange="onChangeAggregateVolumeFraction(this);" />
                                                </logic:equal>
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="3">
                                            <logic:equal name="mixingForm" property="add_fine_aggregate01" value="true">
                                                <div id="fine_aggregate01_properties" class="collapsable-element">
                                                </logic:equal>
                                                <logic:equal name="mixingForm" property="add_fine_aggregate01" value="false">
                                                    <div id="fine_aggregate01_properties" class="collapsable-element hidden">
                                                    </logic:equal>
                                                    <div id="fine_aggregate01_properties-title" class="collapsable-title collapsed"><a onclick="collapseExpand('fine_aggregate01_properties');">Change properties</a>
                                                        <div id="fine_aggregate01_properties-content" class="collapsable-content collapsed">
                                                            <span id="fine_aggregate01_display_name" class="block-displayed">Aggregate source:
                                                                <html:select property="fine_aggregate01_display_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_fine_aggregate01',this.form);">
                                                                    <html:options name="cement_database" property="fine_aggregates" />
                                                                </html:select>
                                                            </span>
                                                            <span id="fine_aggregate01_sg" class="block-displayed">
						Specific gravity:
                                                                <html:text size="6" property="fine_aggregate01_sg" onchange="updateMixVolumeFractions(this.form);" />
                                                            </span>
                                                            <span id="fine_aggregate01_grading_name" class="block-displayed">
						Grading:
                                                                <html:select property="fine_aggregate01_grading_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_fine_aggregate01_grading',this.form)">
                                                                    <html:options name="cement_database" property="fine_aggregate_gradings" />
                                                                </html:select>
                                                            </span>
                                                            <div>
                                                                <table>
                                                                    <tr>
                                                                        <th>Sieve</th>
                                                                        <th>Diameter (mm)</th>
                                                                        <th>Fraction Retained</th>
                                                                    </tr>
                                                                    <% for (int i = 0; i < fine01Grading[0].length; i++) {%>
                                                                    <tr class="fine_aggregate01_grading-line">
                                                                        <td class="fine_aggregate01_grading-sieve_name">
                                                                            <span id="fine_aggregate01_grading-sieve_name_<%=i%>"><%=fine01Grading[0][i]%></span>
                                                                        </td>
                                                                        <td>
                                                                            <% if (i == 0) {%>
                                                                            <span id="fine_aggregate01_grading-min_sieve_diameter_<%=i%>" class="fine_aggregate01_grading-sieve_diameter"><%=fine01Grading[1][i]%></span> - <span id="fine_aggregate01_grading_max_diam"><html:text size="6" property="fine_aggregate01_grading_max_diam"  onchange="checkFineAggregateGradingMaxDiam(this,'01');" /></span>
                                                                            <% } else {%>
                                                                            <span id="fine_aggregate01_grading-min_sieve_diameter_<%=i%>" class="fine_aggregate01_grading-min_sieve_diameter"><%=fine01Grading[1][i]%></span> - <span id="fine_aggregate01_grading-sieve_max_diameter_<%=i - 1%>"><%=fine01Grading[1][i - 1]%></span>
                                                                            <% }%>
                                                                        </td>
                                                                        <td>
                                                                            <span id="fine_aggregate01_grading_massfrac_<%=i%>" class="fine_aggregate01_grading_massfrac"><input type="text" value="<%=fine01Grading[2][i]%>" name="fine_aggregate01_grading_massfrac_<%=i%>" onchange="onChangeFineAggregateGradingMassFrac(this,'01');" size="6"></span>
                                                                        </td>
                                                                    </tr>
                                                                    <% }%>
                                                                    <tr>
                                                                        <td colspan="3">
                                                                            <hr />
                                                                        </td>
                                                                    </tr>
                                                                    <tr>
                                                                        <td colspan="2">
									Total
                                                                        </td>
                                                                        <td>
                                                                            <span id="fine_aggregate01_grading_total_massfrac"><input type="text" name="fine_aggregate01_grading_total_massfrac" value="1.0"  size="6" readonly="readonly" /></span>
                                                                        </td>
                                                                    </tr>
                                                                    <tr>
                                                                        <td colspan="3">
									Name:
                                                                            <span id="new_fine_aggregate01_grading_name"><html:text size="15" property="new_fine_aggregate01_grading_name" /></span>
                                                                            <input type="button" onclick="saveFineGrading(this.form,'01');" value="Save" />
                                                                        </td>
                                                                    </tr>
                                                                </table>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    </td>
                                                    </tr>
                                                    <tr>
                                                        <td>
                                                            <span id="add_fine_aggregate02">
                                                                <html:hidden property="add_fine_aggregate02" />
                                                                <logic:equal name="mixingForm" property="add_fine_aggregate02" value="true">
                                                                    <input type="checkbox" name="add_fine_aggregate02_checkbox" CHECKED onclick="addOrRemoveFineAggregate(this.form,'02');" /> Add Fine Aggregate 2
                                                                    </logic:equal>
                                                                    <logic:equal name="mixingForm" property="add_fine_aggregate02" value="false">
                                                                        <input type="checkbox" name="add_fine_aggregate02_checkbox" onclick="addOrRemoveFineAggregate(this.form,'02');" /> Add Fine Aggregate 2
                                                                    </logic:equal>
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span id="fine_aggregate02_massfrac">
                                                                <logic:equal name="mixingForm" property="add_fine_aggregate02" value="true">
                                                                    <html:text size="6" property="fine_aggregate02_massfrac" onchange="onChangeAggregateMassFraction(this);" />
                                                                </logic:equal>
                                                                <logic:equal name="mixingForm" property="add_fine_aggregate02" value="false">
                                                                    <html:text size="6" property="fine_aggregate02_massfrac" disabled="true" onchange="onChangeAggregateMassFraction(this);" />
                                                                </logic:equal>
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span id="fine_aggregate02_volfrac">
                                                                <logic:equal name="mixingForm" property="add_fine_aggregate02" value="true">
                                                                    <html:text size="6" property="fine_aggregate02_volfrac" onchange="onChangeAggregateVolumeFraction(this);" />
                                                                </logic:equal>
                                                                <logic:equal name="mixingForm" property="add_fine_aggregate02" value="false">
                                                                    <html:text size="6" property="fine_aggregate02_volfrac" disabled="true" onchange="onChangeAggregateVolumeFraction(this);" />
                                                                </logic:equal>
                                                            </span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td colspan="3">
                                                            <logic:equal name="mixingForm" property="add_fine_aggregate02" value="true">
                                                                <div id="fine_aggregate02_properties" class="collapsable-element">
                                                                </logic:equal>
                                                                <logic:equal name="mixingForm" property="add_fine_aggregate02" value="false">
                                                                    <div id="fine_aggregate02_properties" class="collapsable-element hidden">
                                                                    </logic:equal>
                                                                    <div id="fine_aggregate02_properties-title" class="collapsable-title collapsed"><a onclick="collapseExpand('fine_aggregate02_properties');">Change properties</a>
                                                                        <div id="fine_aggregate02_properties-content" class="collapsable-content collapsed">
                                                                            <span id="fine_aggregate02_display_name" class="block-displayed">Aggregate source:
                                                                                <html:select property="fine_aggregate02_display_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_fine_aggregate02',this.form);">
                                                                                    <html:options name="cement_database" property="fine_aggregates" />
                                                                                </html:select>
                                                                            </span>
                                                                            <span id="fine_aggregate02_sg" class="block-displayed">
						Specific gravity:
                                                                                <html:text size="6" property="fine_aggregate02_sg" onchange="updateMixVolumeFractions(this.form);" />
                                                                            </span>
                                                                            <span id="fine_aggregate02_grading_name" class="block-displayed">
						Grading:
                                                                                <html:select property="fine_aggregate02_grading_name" onchange="retrieveURL('/vcctl/operation/prepareMix.do?action=change_fine_aggregate02_grading',this.form)">
                                                                                    <html:options name="cement_database" property="fine_aggregate_gradings" />
                                                                                </html:select>
                                                                            </span>
                                                                            <div>
                                                                                <table>
                                                                                    <tr>
                                                                                        <th>Sieve</th>
                                                                                        <th>Diameter (mm)</th>
                                                                                        <th>Fraction Retained</th>
                                                                                    </tr>
                                                                                    <% for (int i = 0; i < fine02Grading[0].length; i++) {%>
                                                                                    <tr class="fine_aggregate02_grading-line">
                                                                                        <td class="fine_aggregate02_grading-sieve_name">
                                                                                            <span id="fine_aggregate02_grading-sieve_name_<%=i%>"><%=fine02Grading[0][i]%></span>
                                                                                        </td>
                                                                                        <td>
                                                                                            <% if (i == 0) {%>
                                                                                            <span id="fine_aggregate02_grading-min_sieve_diameter_<%=i%>" class="fine_aggregate02_grading-sieve_diameter"><%=fine02Grading[1][i]%></span> - <span id="fine_aggregate02_grading_max_diam"><html:text size="6" property="fine_aggregate02_grading_max_diam"  onchange="checkFineAggregateGradingMaxDiam(this,'02');" /></span>
                                                                                            <% } else {%>
                                                                                            <span id="fine_aggregate02_grading-min_sieve_diameter_<%=i%>" class="fine_aggregate02_grading-min_sieve_diameter"><%=fine02Grading[1][i]%></span> - <span id="fine_aggregate02_grading-sieve_max_diameter_<%=i - 1%>"><%=fine02Grading[1][i - 1]%></span>
                                                                                            <% }%>
                                                                                        </td>
                                                                                        <td>
                                                                                            <span id="fine_aggregate02_grading_massfrac_<%=i%>" class="fine_aggregate02_grading_massfrac"><input type="text" value="<%=fine02Grading[2][i]%>" name="fine_aggregate02_grading_massfrac_<%=i%>" onchange="onChangeFineAggregateGradingMassFrac(this,'02');" size="6"></span>
                                                                                        </td>
                                                                                    </tr>
                                                                                    <% }%>
                                                                                    <tr>
                                                                                        <td colspan="3">
                                                                                            <hr />
                                                                                        </td>
                                                                                    </tr>
                                                                                    <tr>
                                                                                        <td colspan="2">
									Total
                                                                                        </td>
                                                                                        <td>
                                                                                            <span id="fine_aggregate02_grading_total_massfrac"><input type="text" name="fine_aggregate02_grading_total_massfrac" value="1.0"  size="6" readonly="readonly" /></span>
                                                                                        </td>
                                                                                    </tr>
                                                                                    <tr>
                                                                                        <td colspan="3">
									Name:
                                                                                            <span id="new_fine_aggregate02_grading_name"><html:text size="15" property="new_fine_aggregate02_grading_name" /></span>
                                                                                            <input type="button" onclick="saveFineGrading(this.form,'02');" value="Save" />
                                                                                        </td>
                                                                                    </tr>
                                                                                </table>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                    </td>
                                                                    </tr>
                                                                    <tr id="air_line" class="hidden">
                                                                        <td colspan="2">
			Air
                                                                        </td>
                                                                        <td>
                                                                            <span id="air_volfrac"><html:text size="6" property="air_volfrac" /></span>
                                                                        </td>
                                                                    </tr>
                                                                    </table>
                                                                    <span id="coarse_aggregate01_grading"><html:hidden property="coarse_aggregate01_grading" /></span>
                                                                    <span id="coarse_aggregate02_grading"><html:hidden property="coarse_aggregate02_grading" /></span>
                                                                    <span id="fine_aggregate01_grading"><html:hidden property="fine_aggregate01_grading" /></span>
                                                                    <span id="fine_aggregate02_grading"><html:hidden property="fine_aggregate02_grading" /></span>
                                                                    <span id="binder_sg"><html:hidden property="binder_sg" /></span>