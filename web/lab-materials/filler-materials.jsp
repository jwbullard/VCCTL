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
	selectSubTab(3);
</script>

<h3>Filler Material Inventory</h3>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<html:form action="/lab-materials/editFillerMaterials.do" method="POST" enctype="multipart/form-data">
    <fieldset id="edit_inert_filler" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_inert_filler');"><b>Edit or create an inert filler</b></a><span id="filler-materials-inert" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="inertFiller">
				Name:
                <nested:select property="name" onchange="onChangeInertFiller(this);" styleClass="inert_filler-element-to-reload" styleId="inert_filler_list">
                    <option value="">New inert filler&hellip</option>
                    <nested:options name="cement_database" property="inert_fillers" />
                </nested:select><span id="filler-materials-inert-name" class="help-icon"></span>
                <div id="inert_filler_specific_gravity" class="inert_filler-element-to-reload">
					Specific gravity: <nested:text property="specific_gravity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFillerMaterials.do?action=update_inert_filler_characteristics',this.form,'inert_filler-characteristic-value-to-update');" />
                    <span id="filler-materials-inert-sg" class="help-icon"></span></div><br/>
				Particle Size Distribution (PSD):
                <nested:select property="psd" styleClass="inert_filler-element-to-reload" styleId="inert_filler_psds_list">
                    <nested:options name="cement_database" property="psds" />
                </nested:select><span id="filler-materials-inert-psd" class="help-icon"></span>
                <div id="inert_filler_description" class="inert_filler-element-to-reload">
					Description:<br />
                    <nested:textarea property="description" style="width:100%" rows="4" cols="40" />
                </div>
                <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editFillerMaterials.do?action=change_inert_filler',this.form,'inert_filler-element-to-reload');" id="cancel_inert_filler_changes" />
                <input type="button" value="Save" onclick="saveInertFiller(this.form);" id="save_inert_filler" />
                <input type="button" value="Save as..." onclick="saveInertFillerAs(this.form);" id="save_inert_filler_as" />
                <input type="button" value="Delete" onclick="deleteInertFiller(this.form);" id="delete_inert_filler" /><span id="filler-materials-inert-save" class="help-icon"></span>
            </nested:nest>
        </div>
    </fieldset>
</html:form>

<!-- Tooltip Help -->
<div id="filler-materials-inert_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of inert filler in the virtual laboratory.  Inert filler
        is considered to be any solid that does not participate in hydration reactions.
    </p>
</div>
<div id="filler-materials-inert-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing inert filler, choose its name from the pull-down menu.
        To create a new inert filler, choose "New inert filler..." from the pull-down menu.
    </p>
</div>
<div id="filler-materials-inert-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the filler, i.e., its density relative to the density of water.
    </p>
</div>
<div id="filler-materials-inert-psd_tt" class="tooltip" style="display:none">
    <p>View or edit the particle size distribution for the inert filler. Currently, the different PSDs available are given by a name (associated material or other descriptive name). <b>Note</b>: The name chosen in the pull-down menu affects only the PSD of the filler, not its chemical composition or other characteristics.
    </p>
</div>
<div id="filler-materials-inert-save_tt" class='tooltip' style="display:none">
    <ol>
        <li>Press the "Cancel" button to cancel any changes made to the characteristics of a filler.
        </li>
        <li>Press the "Save" button to save the changes made as the same filler. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new characteristics as a new filler, and then give a unique name to the new material when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected inert filler.
        </li>
    </ol>
</div>
<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("filler-materials-inert", "filler-materials-inert_tt");
    Tooltip.add("filler-materials-inert-name", "filler-materials-inert-name_tt");
    Tooltip.add("filler-materials-inert-sg", "filler-materials-inert-sg_tt");
    Tooltip.add("filler-materials-inert-psd", "filler-materials-inert-psd_tt");
    Tooltip.add("filler-materials-inert-save", "filler-materials-inert-save_tt");
</script>
