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
	selectSubTab(1);
</script>

<h3>Slag Material Inventory</h3>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<html:form action="/lab-materials/editSlagMaterials.do" method="POST" enctype="multipart/form-data">
    <fieldset id="edit_slag" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_slag');"><b>Edit or create a slag</b></a><span id="slag-materials-slag" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="slag">
				Name:
                <nested:select property="name" onchange="onChangeSlag(this);" styleClass="slag-element-to-reload" styleId="slag_list">
                    <option value="">New slag&hellip</option>
                    <nested:options name="cement_database" property="slags" />
                </nested:select><span id="slag-materials-slag-name" class="help-icon"></span>
                <div id="slag_specific_gravity" class="slag-element-to-reload">
					Specific gravity (SG): <nested:text property="specific_gravity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" /><span id="slag-materials-slag-sg" class="help-icon"></span>
                </div>
				Particle Size Distribution (PSD):
                <nested:select property="psd" styleClass="slag-element-to-reload" styleId="slag_psds_list">
                    <nested:options name="cement_database" property="psds" />
                </nested:select><span id="lab-materials-slag-psd" class="help-icon"></span>
                <fieldset id="slag_properties_description_fieldset" class="collapsed">
                    <legend class="collapsable-title collapsed"><a onclick="collapseExpand('slag_properties_description_fieldset');"><b>Slag properties and description</b></a><span id="lab-materials-slag-table" class="help-icon"></span></legend>
                    <div class="collapsable-content collapsed" id="slag_properties_description">
                        <table class="list-table">
                            <thead>
                                <tr>
                                    <th>
										Property
                                    </th>
                                    <th>
										Slag
                                    </th>
                                    <th>
										Slag gel hydration product
                                    </th>
                                </tr>
                            </thead>
                            <tr>
                                <td>
									Molecular mass (g/mol)
                                </td>
                                <td id="slag_molecular_mass" class="slag-element-to-reload">
                                    <nested:text property="molecular_mass" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" />
                                </td>
                                <td id="slag_hp_molecular_mass" class="slag-element-to-reload">
                                    <nested:text property="hp_molecular_mass" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Density (g/cm<sup>3</sup>)
                                </td>
                                <td id="slag_density" class="slag-characteristic-value-to-update slag-element-to-reload">
                                    <nested:text property="density" readonly="true"/>
                                </td>
                                <td id="slag_hp_density" class="slag-element-to-reload">
                                    <nested:text property="hp_density" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Molar volume (cm<sup>3</sup>/mol)
                                </td>
                                <td id="slag_molar_volume" class="slag-characteristic-value-to-update slag-element-to-reload">
                                    <nested:text property="molar_volume" readonly="true" />
                                </td>
                                <td id="slag_hp_molar_volume" class="slag-characteristic-value-to-update slag-element-to-reload">
                                    <nested:text property="hp_molar_volume" readonly="true" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Ca/Si molar ratio
                                </td>
                                <td id="slag_casi_mol_ratio" class="slag-element-to-reload">
                                    <nested:text property="casi_mol_ratio" />
                                </td>
                                <td id="slag_hp_casi_mol_ratio" class="slag-element-to-reload">
                                    <nested:text property="hp_casi_mol_ratio" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Si per mole of slag<span id="slag-materials-slag-table-si" class="help-icon"></span>
                                </td>
                                <td id="slag_si_per_mole" class="slag-element-to-reload">
                                    <nested:text property="si_per_mole" />
                                </td>
                                <td/>
                            </tr>
                            <tr>
                                <td>
									H<sub>2</sub>O/Si molar ratio
                                </td>
                                <td/>
                                <td id="slag_hp_h2osi_mol_ratio" class="slag-element-to-reload">
                                    <nested:text property="hp_h2osi_mol_ratio" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									C<sub>3</sub>A per mole of slag<span id="slag-materials-slag-table-c3a" class="help-icon"></span>
                                </td>
                                <td/>
                                <td id="slag_c3a_per_mole" class="slag-element-to-reload">
                                    <nested:text property="c3a_per_mole" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Base slag reactivity<span id="slag-materials-slag-table-reactivity" class="help-icon"></span>
                                </td>
                                <td id="slag_base_slag_reactivity" class="slag-element-to-reload">
                                    <nested:text property="base_slag_reactivity" />
                                </td>
                                <td/>
                            </tr>
                        </table>
                        <div id="slag_description" class="slag-element-to-reload">
							Description:<span id="slag-materials-slag-description" class="help-icon"></span><br />
                            <nested:textarea property="description" style="width:100%" rows="6" cols="40" />
                        </div>
                    </div>
                </fieldset>
            </nested:nest>
            <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editSlagMaterials.do?action=change_slag',this.form,'slag-element-to-reload');" id="cancel_slag_changes" />
            <input type="button" value="Save" onclick="saveSlag(this.form);" id="save_slag" />
            <input type="button" value="Save as..." onclick="saveSlagAs(this.form);" id="save_slag_as" />
            <input type="button" value="Delete" onclick="deleteSlag(this.form);" id="delete_slag" /><span id="slag-materials-slag-save" class="help-icon"></span>
        </div>
    </fieldset>

</html:form>

<!-- Tooltip Help -->

<div id="slag-materials-slag_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of ground granulated blast furnace slags (GGBS) in the virtual laboratory.
    </p>
</div>
<div id="slag-materials-slag-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing slag, choose its name from the pull-down menu.
    </p>
</div>
<div id="slag-materials-slag-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the slag, i.e., its density relative to the density of water.
    </p>
</div>
<div id="slag-materials-slag-psd_tt" class="tooltip" style="display:none">
    <p>View or edit the particle size distribution for the slag powder. Currently, the different PSDs available are given by a name (associated material or other descriptive name). <b>Note</b>: The name chosen in the pull-down menu affects only the PSD of the slag, not its chemical composition or other characteristics.
    </p>
</div>
<div id="slag-materials-slag-table_tt" class="tooltip" style="display:none">
    <p>View or edit the physicochemical properties of the slag <b>and</b> of its hydration product.
    </p>
</div>
<div id="slag-materials-slag-table-si_tt" class="tooltip" style="display:none">
    <p>
        <b>Si per mole of slag</b>. Specifies the number of moles of Si per mole of slag.
    </p>
</div>
<div id="slag-materials-slag-table-c3a_tt" class="tooltip" style="display:none">
    <p>
        <b>C<sub>3</sub>A per mole of slag</b>. Specifies the number of moles of C<sub>3</sub>A per mole of slag.
    </p>
</div>
<div id="slag-materials-slag-table-reactivity_tt" class="tooltip" style="display:none">
    <p>
        <b>Base slag reactivity</b>. This is a dimensionless, nonnegative real number that specifies how readily the slag reacts with water, relative to the default slag reactivity that is specified in the hydration parameter file. A value of 1.0 leaves the reactivity unchanged, a value of X makes the slag reactivity X times as fast as the default value.
    </p>
</div>
<div id="slag-materials-slag-description_tt" class="tooltip" style="display:none">
    <p>View or edit a verbal description of the slag material. This is for user information purposes only, and does not factor into any of the calculations performed by VCCTL.
    </p>
</div>
<div id="slag-materials-slag-save_tt" class='tooltip' style="display:none">
    <ol>
        <li>Press the "Cancel" button to cancel any changes made to the characteristics of a slag.
        </li>
        <li>Press the "Save" button to save the changes made as the same slag. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new characteristics as a new slag, and then give a unique name to the new material when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected slag.
        </li>
    </ol>
</div>
<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("slag-materials-overview", "slag-materials-overview_tt");
    Tooltip.add("slag-materials-slag", "slag-materials-slag_tt");
    Tooltip.add("slag-materials-slag-name", "slag-materials-slag-name_tt");
    Tooltip.add("slag-materials-slag-sg", "slag-materials-slag-sg_tt");
    Tooltip.add("slag-materials-slag-psd", "slag-materials-slag-psd_tt");
    Tooltip.add("slag-materials-slag-table", "slag-materials-slag-table_tt");
    Tooltip.add("slag-materials-slag-table-si", "slag-materials-slag-table-si_tt");
    Tooltip.add("slag-materials-slag-table-c3a", "slag-materials-slag-table-c3a_tt");
    Tooltip.add("slag-materials-slag-table-reactivity", "slag-materials-slag-table-reactivity_tt");
    Tooltip.add("slag-materials-slag-description", "slag-materials-slag-description_tt");
    Tooltip.add("slag-materials-slag-save", "slag-materials-slag-save_tt");
</script>
