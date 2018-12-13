<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-nested" prefix="nested" %>

<%@page import="nist.bfrl.vcctl.database.*" %>
<%@page import="java.util.*" %>

<html:xhtml />

<script type="text/javascript">
    selectTab(1);
    if (!$$('#subtabs-right ul')[0] || !$$('#subtabs-right ul')[0].hasChildNodes() || ($$('#subtabs-right ul li')[0] && $$('#subtabs-right ul li')[0].id != "cement-materials")) {
        var titles = new Array();
        titles[0] = "Cements";
        titles[1] = "Slags";
        titles[2] = "Fly Ashes";
        titles[3] = "Fillers";
        titles[4] = "Aggregates";
        var ids = new Array();
        ids[0] = "cement-materials";
        ids[1] = "slag-materials";
        ids[2] = "flyash-materials";
        ids[3] = "filler-materials";
        ids[4] = "aggregate-materials";
        var urls = new Array();
        urls[0] = "<%=request.getContextPath()%>/lab-materials/initializeCementMaterials.do";
        urls[1] = "<%=request.getContextPath()%>/lab-materials/initializeSlagMaterials.do";
        urls[2] = "<%=request.getContextPath()%>/lab-materials/initializeFlyAshMaterials.do";
        urls[3] = "<%=request.getContextPath()%>/lab-materials/initializeFillerMaterials.do";
        urls[4] = "<%=request.getContextPath()%>/lab-materials/initializeAggregateMaterials.do";
        createSubTabsMenu(titles,ids,urls);
    }
    $('subtab-menu').show();
    $('top-border').hide();
    selectSubTab(4);
</script>

<h3>Aggregate Material Inventory</h3>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<html:form action="/lab-materials/editAggregateMaterials.do" method="POST" enctype="multipart/form-data">
    <fieldset id="edit_aggregate" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_aggregate');"><b>Edit or create aggregate sources</b></a><span id="aggregate-materials-aggregate" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <fieldset id="edit_coarse_aggregate" class="collapsed">
                <legend class="collapsable-title collapsed"><a onclick="collapseExpand('edit_coarse_aggregate');"><b>Coarse aggregate</b></a></legend>
                <div class="collapsable-content collapsed">
                    <nested:nest property="coarseAggregate">
				Coarse aggregate source:
                        <nested:select property="display_name" onchange="onChangeCoarseAggregate(this);"  styleClass="coarse_aggregate-element-to-reload" styleId="coarse_aggregate_list">
                            <option value="">New coarse aggregate&hellip</option>
                            <nested:options name="cement_database" property="coarse_aggregates" />
                        </nested:select><span id="aggregate-materials-coarse-aggregate-name" class="help-icon"></span>
                        <input type="hidden" name="action" />
                        <div id="coarse_aggregate_name" class="coarse_aggregate-element-to-reload">
                        <nested:hidden property="name"></nested:hidden>
                        </div>
                        <div id="coarse_aggregate_zip_file" class="coarse_aggregate-element-to-reload">
					Upload data from a ZIP file for the coarse aggregate: <html:file property="uploaded_coarse_aggregate_file" accept="zip" onchange="AIM.submit(this.form, {'onStart':startUploadCoarseAggregateCallback, 'onComplete':completeUploadCoarseAggregateCallback}); this.form.submit();" styleId="coarse_aggregate_zip_file_input"/>
                        </div>
                        <fieldset id="coarse_aggregate_image" class="coarse_aggregate-element-to-reload">
                            <legend><b>Image and shape data</b></legend>
                            <table>
                            <tr>
                                <th width="45%">Image</th>
                                <th width="45%">Shape Data</th>
                            </tr>
                            <tr>
                                <td width="45%"><img src="/vcctl/image/${coarseAggName}.gif" width="256" alt="No image available" /></td>
                                <td width="45%"><nested:textarea property="shapestatsString" rows="10" cols="46" styleId="aggregate_shapestats" styleClass="coarse_aggregate-element-to-reload" /></td>
                            </tr>
                            </table>
                        </fieldset>
                        <nested:hidden property="type"></nested:hidden>
                        <div id="coarse_aggregate_specific_gravity" class="coarse_aggregate-element-to-reload">
					Specific gravity: <nested:text property="specific_gravity" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" />
                        </div><br/>
                        <div id="coarse_aggregate_bulk_modulus" class="coarse_aggregate-element-to-reload">
					Bulk modulus: <nested:text property="bulk_modulus" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" /> GPa
                        </div><br/>
                        <div id="coarse_aggregate_shear_modulus" class="coarse_aggregate-element-to-reload">
					Shear modulus: <nested:text property="shear_modulus" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" /> GPa
                        </div><br/>
                        <div id="coarse_aggregate_conductivity" class="coarse_aggregate-element-to-reload">
					Conductivity: <nested:text property="conductivity" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" />
                        </div><br/>
                        <div id="coarse_aggregate_description" class="coarse_aggregate-element-to-reload">
					Description:<br />
                            <nested:textarea property="infString" style="width:100%" rows="4" cols="40" />
                        </div>
                        <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editAggregateMaterials.do?action=change_coarse_aggregate',this.form,'coarse_aggregate-element-to-reload');" id="cancel_coarse_aggregate_changes" />
                        <input type="button" value="Save" onclick="saveCoarseAggregate(this.form);" id="save_coarse_aggregate" />
                        <input type="button" value="Save as..." onclick="saveCoarseAggregateAs(this.form);" id="save_coarse_aggregate_as" />
                        <input type="button" value="Delete" onclick="deleteCoarseAggregate(this.form);" id="delete_coarse_aggregate" /><span id="aggregate-materials-coarse-aggregate-save" class="help-icon"></span>
                    </nested:nest>
                </div>
            </fieldset>
            <fieldset id="edit_fine_aggregate" class="collapsed">
                <legend class="collapsable-title collapsed"><a onclick="collapseExpand('edit_fine_aggregate');"><b>Fine aggregate</b></a></legend>
                <div class="collapsable-content collapsed">
                    <nested:nest property="fineAggregate">
				Fine aggregate source:
                        <nested:select property="display_name" onchange="onChangeFineAggregate(this);"  styleClass="fine_aggregate-element-to-reload" styleId="fine_aggregate_list">
                            <option value="">New fine aggregate&hellip</option>
                            <nested:options name="cement_database" property="fine_aggregates" />
                        </nested:select><span id="aggregate-materials-fine-aggregate-name" class="help-icon"></span>
                        <div id="fine_aggregate_name" class="fine_aggregate-element-to-reload">
                        <nested:hidden property="name"></nested:hidden>
                        </div>
                        <div id="fine_aggregate_zip_file" class="fine_aggregate-element-to-reload">
					Upload data from a ZIP file for the fine aggregate: <html:file property="uploaded_fine_aggregate_file" accept="zip" onchange="AIM.submit(this.form, {'onStart':startUploadFineAggregateCallback, 'onComplete':completeUploadFineAggregateCallback}); this.form.submit();" styleId="fine_aggregate_zip_file_input"/>
                        </div>
                        <fieldset id="fine_aggregate_image" class="fine_aggregate-element-to-reload">
                            <legend><b>Image and shape data</b></legend>
                            <table>
                            <tr>
                                <th width="45%">Image</th>
                                <th width="45%">Shape Data</th>
                            </tr>
                            <tr>
                                <td width="45%"><img src="/vcctl/image/${fineAggName}.gif" width="256" alt="No image available" /></td>
                                <td width="45%"><nested:textarea property="shapestatsString" rows="10" cols="46" styleId="aggregate_shapestats" styleClass="fine_aggregate-element-to-reload" /></td>
                            </tr>
                            </table>
                        </fieldset>
                        <nested:hidden property="type"></nested:hidden>
                        <div id="fine_aggregate_specific_gravity" class="fine_aggregate-element-to-reload">
					Specific gravity: <nested:text property="specific_gravity" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" />
                        </div><br/>
                        <div id="fine_aggregate_bulk_modulus" class="fine_aggregate-element-to-reload">
					Bulk modulus: <nested:text property="bulk_modulus" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" /> GPa
                        </div><br/>
                        <div id="fine_aggregate_shear_modulus" class="fine_aggregate-element-to-reload">
					Shear modulus: <nested:text property="shear_modulus" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" /> GPa
                        </div><br/>
                        <div id="fine_aggregate_conductivity" class="fine_aggregate-element-to-reload">
					Conductivity: <nested:text property="conductivity" size="6" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" />
                        </div><br/>
                        <div id="fine_aggregate_description" class="fine_aggregate-element-to-reload">
					Description:<br />
                            <nested:textarea property="infString" style="width:100%" rows="4" cols="40" />
                        </div>
                        <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editAggregateMaterials.do?action=change_fine_aggregate',this.form,'fine_aggregate-element-to-reload');" id="cancel_fine_aggregate_changes" />
                        <input type="button" value="Save" onclick="saveFineAggregate(this.form);" id="save_fine_aggregate" />
                        <input type="button" value="Save as..." onclick="saveFineAggregateAs(this.form);" id="save_fine_aggregate_as" />
                        <input type="button" value="Delete" onclick="deleteFineAggregate(this.form);" id="delete_fine_aggregate" /><span id="aggregate-materials-fine-aggregate-save" class="help-icon"></span>
                    </nested:nest>
                </div>
            </fieldset>
        </div>
    </fieldset>
</html:form>

<!-- Tooltip Help -->
<div id="aggregate-materials-aggregate_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of coarse and fine aggregate in the virtual laboratory.
    </p>
</div>
<div id="aggregate-materials-coarse-aggregate-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing coarse aggregate, choose its name from the pull-down menu.
        To create a new coarse aggregate, choose "New coarse aggregate..." from the pull-down menu.
    </p>
</div>
<div id="aggregate-materials-coarse-aggregate-save_tt" class='tooltip' style="display:none">
    <ol>
        <li>Press the "Cancel" button to cancel any changes made to the characteristics of an aggregate.
        </li>
        <li>Press the "Save" button to save the changes made as the same coarse aggregate. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new characteristics as a new coarse aggregate, and then give a unique name to the new material when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected coarse aggregate.
        </li>
    </ol>
</div>
<div id="aggregate-materials-fine-aggregate-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing fine aggregate, choose its name from the pull-down menu.
        To create a new fine aggregate, choose "New fine aggregate..." from the pull-down menu.
    </p>
</div>
<div id="aggregate-materials-fine-aggregate-save_tt" class='tooltip' style="display:none">
    <ol>
        <li>Press the "Cancel" button to cancel any changes made to the characteristics of an aggregate.
        </li>
        <li>Press the "Save" button to save the changes made as the same fine aggregate. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new characteristics as a new fine aggregate, and then give a unique name to the new material when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected fine aggregate.
        </li>
    </ol>
</div>
<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("aggregate-materials-aggregate", "aggregate-materials-aggregate_tt");
    Tooltip.add("aggregate-materials-coarse-aggregate-name", "aggregate-materials-coarse-aggregate-name_tt");
    Tooltip.add("aggregate-materials-coarse-aggregate-save", "aggregate-materials-coarse-aggregate-save_tt");
    Tooltip.add("aggregate-materials-fine-aggregate-name", "aggregate-materials-fine-aggregate-name_tt");
    Tooltip.add("aggregate-materials-fine-aggregate-save", "aggregate-materials-fine-aggregate-save_tt");
</script>
