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
	selectSubTab(2);
</script>

<h3>Fly Ash Material Inventory</h3>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<html:form action="/lab-materials/editFlyAshMaterials.do" method="POST" enctype="multipart/form-data">
    <fieldset id="edit_fly_ash" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_fly_ash');"><b>Edit or create a fly ash</b></a><span id="flyash-materials-flyash" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="flyAsh">
				Name:
                <nested:select property="name" onchange="onChangeFlyAsh(this);" styleClass="fly_ash-element-to-reload" styleId="fly_ash_list">
                    <option value="">New fly ash&hellip</option>
                    <nested:options name="cement_database" property="flyashs" />
                </nested:select><span id="flyash-materials-flyash-name" class="help-icon"></span>
                <div id="fly_ash_specific_gravity" class="fly_ash-element-to-reload">
					Specific gravity (SG):
                    <nested:text property="specific_gravity" /><span id="flyash-materials-flyash-sg" class="help-icon"></span>
                </div>
                <div id="fly_ash_psd">
                    Particle Size Distribution (PSD):
                    <nested:select property="psd" styleClass="fly_ash-element-to-reload" styleId="fly_ash_psds_list">
                        <nested:options name="cement_database" property="psds" />
                    </nested:select>
                    <span id="flyash-materials-flyash-psd" class="help-icon"></span>
                </div>
                <div id="fly_ash_distribute_phases">
                    Distribute flyash phases randomly:<span id="flyash-materials-flyash-distribute" class="help-icon"></span>
                </div>
                <div id="fly_ash_random_distribution_mode" class="fly_ash-element-to-reload">
                    <nested:radio property="distribute_phases_by" value="0" /> on particle basis, OR
                    <nested:radio property="distribute_phases_by" value="1" /> on pixel basis
                </div>
                <fieldset id="fly_ash_properties_description_fieldset" class="collapsed">
                    <legend class="collapsable-title collapsed"><a onclick="collapseExpand('fly_ash_properties_description_fieldset');"><b>Fly ash properties and description</b></a></legend>
                    <div class="collapsable-content collapsed" id="fly_ash_properties_description">
			<table class="list-table">
                            <thead>
                                <tr>
                                    <th>
										Phase<span id="flyash-materials-flyash-table-phase" class="help-icon"></span>
                                    </th>
                                    <th>
										Fraction<span id="flyash-materials-flyash-table-fraction" class="help-icon"></span>
                                    </th>
                                </tr>
                            </thead>
                            <tr>
                                <td>
									Aluminosilicate glass
                                </td>
                                <td id="fly_ash_aluminosilicate_glass_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="aluminosilicate_glass_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Calcium Aluminum Disilicate
                                </td>
                                <td id="fly_ash_calcium_aluminum_disilicate_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="calcium_aluminum_disilicate_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Tricalcium Aluminate
                                </td>
                                <td id="fly_ash_tricalcium_aluminate_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="tricalcium_aluminate_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Calcium Chloride
                                </td>
                                <td id="fly_ash_calcium_chloride_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="calcium_chloride_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Silica
                                </td>
                                <td id="fly_ash_silica_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="silica_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Anhydrite (CaSO4)
                                </td>
                                <td id="fly_ash_anhydrite_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="anhydrite_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <hr/>
                                </td>
                            </tr>
                            <tr>
                                <td>
									Sum
                                </td>
                                <td id="fly_ash_sum_of_fractions" class="fly_ash-vol_frac-sum fly_ash-element-to-reload">
                                    <nested:text property="sum_of_fractions" readonly="true" />
                                </td>
                            </tr>
                        </table>
                        <div id="fly_ash_description" class="fly_ash-element-to-reload">
							Description:<span id="flyash-materials-flyash-description" class="help-icon"></span><br />
                            <nested:textarea property="description" style="width:100%" rows="4" cols="40" />
                        </div>
                    </div>
                </fieldset>
                <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editFlyAshMaterials.do?action=change_fly_ash',this.form,'fly_ash-element-to-reload');" id="cancel_fly_ash_changes" />
                <input type="button" value="Save" onclick="saveFlyAsh(this.form);" id="save_fly_ash" />
                <input type="button" value="Save as..." onclick="saveFlyAshAs(this.form);" id="save_fly_ash_as" />
                <input type="button" value="Delete" onclick="deleteFlyAsh(this.form);" id="delete_fly_ash" /><span id="flyash-materials-flyash-save" class="help-icon"></span>
            </nested:nest>
        </div>
    </fieldset>

</html:form>

<!-- Tooltip Help -->
<div id="flyash-materials-flyash_tt" class="tooltip" style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of fly ashes in the virtual laboratory.
    </p>
</div>
<div id="flyash-materials-flyash-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing fly ash, choose its name from the pull-down menu.
    </p>
</div>
<div id="flyash-materials-flyash-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the fly ash, i.e., its density relative to the density of water.
    </p>
</div>
<div id="flyash-materials-flyash-psd_tt" class="tooltip" style="display:none">
    <p>View or edit the particle size distribution for the fly ash powder. Currently, the different PSDs available are given by a name (associated material or other descriptive name). <b>Note</b>: The name chosen in the pull-down menu affects only the PSD of the fly ash, not its chemical composition or other characteristics.
    </p>
</div>
<div id="flyash-materials-flyash-distribute_tt" class="tooltip" style="display:none">
    <p>When the fly ash is added to a mix, each fly ash particle can be assigned a single phase at random based on the volume fractions in the table below (<b>particle basis</b>). Alternatively, each particle can be composed of multiple phases proportioned according to the fractions in the table below (<b>pixel basis</b>). It is up to the user to decide, based on microscopic examination of the particles, which scenario best represents the distribution of fly ash phases.
    </p>
</div>
<div id="flyash-materials-flyash-table-phase_tt" class="tooltip" style="display:none">
    <p>There are seven phases recognized by VCCTL for fly ash materials. Six of them are given in this column. The seventh phase is considered to be inert filler. Any fly ash material that has not been assigned one of the six listed phases is considered to be inert filler.
    </p>
</div>
<div id="flyash-materials-flyash-table-fraction_tt" class="tooltip" style="display:none">
    <p>View or edit the <b>volume fraction</b>, on a total fly ash volume basis, for each phase in the first column. If the sum of the fractions in this column is less than 1.0, the remaning volume fraction will be assigned as inert filler.
    </p>
</div>
<div id="flyash-materials-flyash-description_tt" class="tooltip" style="display:none">
    <p>View or edit a verbal description of the fly ash material. This is for user information purposes only, and does not factor into any of the calculations performed by VCCTL.
    </p>
</div>
<div id="flyash-materials-flyash-save_tt" class='tooltip' style="display:none">
    <ol>
        <li>Press the "Cancel" button to cancel any changes made to the characteristics of a fly ash.
        </li>
        <li>Press the "Save" button to save the changes made as the same fly ash. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new characteristics as a new fly ash, and then give a unique name to the new material when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected fly ash.
        </li>
    </ol>
</div>
<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("flyash-materials-flyash", "flyash-materials-flyash_tt");
    Tooltip.add("flyash-materials-flyash-name", "flyash-materials-flyash-name_tt");
    Tooltip.add("flyash-materials-flyash-sg", "flyash-materials-flyash-sg_tt");
    Tooltip.add("flyash-materials-flyash-psd", "flyash-materials-flyash-psd_tt");
    Tooltip.add("flyash-materials-flyash-distribute", "flyash-materials-flyash-distribute_tt");
    Tooltip.add("flyash-materials-flyash-table-phase", "flyash-materials-flyash-table-phase_tt");
    Tooltip.add("flyash-materials-flyash-table-fraction", "flyash-materials-flyash-table-fraction_tt");
    Tooltip.add("flyash-materials-flyash-description", "flyash-materials-flyash-description_tt");
    Tooltip.add("flyash-materials-flyash-save", "flyash-materials-flyash-save_tt");
</script>
