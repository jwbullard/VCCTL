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
    selectTab(3);
	if (!$$('#subtabs-right ul')[0] || !$$('#subtabs-right ul')[0].hasChildNodes() || ($$('#subtabs-right ul li')[0] && $$('#subtabs-right ul li')[0].id != "lab-materials")) {
		var titles = new Array();
		titles[0] = "Cements";
		titles[1] = "Slags";
                titles[2] = "Fly Ashes";
                titles[3] = "Fillers";
                titles[4] = "Aggregates";
		var ids = new Array();
		ids[0] = "lab-materials";
		ids[1] = "lab-materials";
                ids[2] = "lab-materials";
		ids[3] = "lab-materials";
                ids[4] = "lab-materials";
		var urls = new Array();
		urls[0] = "<%=request.getContextPath()%>/lab-materials/initializeLabMaterials.do";
		urls[1] = "<%=request.getContextPath()%>/lab-materials/initializeLabMaterials.do";
                urls[2] = "<%=request.getContextPath()%>/lab-materials/initializeLabMaterials.do";
		urls[3] = "<%=request.getContextPath()%>/lab-materials/initializeLabMaterials.do";
                urls[4] = "<%=request.getContextPath()%>/lab-materials/initializeLabMaterials.do";
		createSubTabsMenu(titles,ids,urls);
	}
	$('subtab-menu').show();
	$('top-border').hide();
	selectSubTab(0);
</script>

<h3>Material Inventory</h3><span id="lab-materials-overview" class="help-icon"></span>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<html:form action="/lab-materials/editLabMaterials.do" method="POST" enctype="multipart/form-data">
    <fieldset id="edit_cement" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_cement');">Edit or create a cement</a><span id="lab-materials-cement" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="cement">
				Name: 
                <nested:select property="name" onchange="onChangeCement(this);" styleClass="cement-element-to-reload" styleId="cement_list" >
                    <option value="">New cement&hellip</option>
                    <nested:options name="cement_database" property="cements" />
                </nested:select><span id="lab-materials-cement-name" class="help-icon"></span>
                <br/>
                <input type="hidden" name="action" />
                <div id="cement_zip_file" class="cement-element-to-reload">
					Upload data from a ZIP file for the cement: <html:file property="uploaded_file" accept="zip" onchange="AIM.submit(this.form, {'onStart':startUploadCallback, 'onComplete':completeUploadCallback}); this.form.submit();" styleId="cement_zip_file_input"/>
                </div>
                <fieldset id="cement_data_fieldset" class="collapsed">
                    <legend class="collapsable-title collapsed"><a onclick="collapseExpand('cement_data_fieldset');">Cement data</a><span id="lab-materials-cement-data" class="help-icon"></span></legend>
                    <div class="collapsable-content collapsed" id="cement_data">
                        <bean:define name="labMaterialsForm" id="cemName" property="cement.name" />
                        Image Name: <%=cemName%>
                        <html:image src="/vcctl/lab-materials/ImageGetter?cemName=<%=cemName%>" alt="Should be an image" styleClass="cement-element-to-reload" />
                        PSD: <span id="lab-materials-cement-data-psd" class="help-icon"></span>
                        <nested:select property="psd" styleId="cement_psd" styleClass="cement-element-to-reload">
                            <nested:options name="cement_database" property="psds" />
                        </nested:select>
                        <br/>
						Alkali: 
                        <nested:select property="alkaliFile" styleId="cement_alkali" styleClass="cement-element-to-reload">
                            <nested:options name="cement_database" property="alkali_characteristics_files" />
                        </nested:select>

                        <table>
                            <tr>
                                <th>PFC<span id="lab-materials-cement-data-pfc" class="help-icon"></span></th>
                                <th>X-ray Diffraction Data<span id="lab-materials-cement-data-xray" class="help-icon"></span></th>
                            </tr>
                            <tr>
                                <td><nested:textarea property="pfcString" rows="10" cols="14" styleId="cement_pfc" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="xrdString" rows="10" cols="46" styleId="cement_xray_diffraction_data" styleClass="cement-element-to-reload" /></td>
                            </tr>
                        </table>
                        <table>
                            <tr>
                                <th>Sil<span id="lab-materials-cement-data-sil" class="help-icon"></span></th>
                                <th>C<sub>3</sub>S<span id="lab-materials-cement-data-c3s" class="help-icon"></span></th>
                                <th>C<sub>4</sub>AF<span id="lab-materials-cement-data-c4af" class="help-icon"></span></th>
                                <th>C<sub>3</sub>A<span id="lab-materials-cement-data-c3a" class="help-icon"></span></th>
                            </tr>
                            <tr>
                                <td><nested:textarea property="silString" rows="10" cols="13" styleId="cement_sil" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="c3sString" rows="10" cols="13" styleId="cement_c3s" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="c4fString" rows="10" cols="13" styleId="cement_c4af" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="c3aString" rows="10" cols="13" styleId="cement_c3a" styleClass="cement-element-to-reload" /></td>
                            </tr>
                        </table>
                        <table>
                            <tr>
                                <th>Na<sub>2</sub>SO<sub>4</sub><span id="lab-materials-cement-data-na2so4" class="help-icon"></span></th>
                                <th>K<sub>2</sub>SO<sub>4</sub><span id="lab-materials-cement-data-k2so4" class="help-icon"></span></th>
                                <th>Alu<span id="lab-materials-cement-data-alu" class="help-icon"></span></th>
                            </tr>
                            <tr>
                                <td><nested:textarea property="n2oString" rows="10" cols="13" styleId="cement_na2o" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="k2oString" rows="10" cols="13" styleId="cement_legend" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="aluString" rows="10" cols="13" styleId="cement_alu" styleClass="cement-element-to-reload" /></td>
                            </tr>
                        </table>
                    </div>
                </fieldset>
                <fieldset id="sulfate_mass_fractions" class="cement-element-to-reload">
                    <legend>Mass fractions of sulfates<span id="lab-materials-cement-data-sulfates" class="help-icon"></span></legend>
					Dihydrate
                    <nested:text property="dihyd" size="8" styleId="cement_dihydrate" />
					Hemihydrate
                    <nested:text property="hemihyd" size="8" styleId="cement_hemihydrate" />
					Anhydrite
                    <nested:text property="anhyd" size="8" styleId="cement_anhydrite" />
                </fieldset>
                <input type="button" value="Cancel" onclick="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=change_cement',this.form,'cement-element-to-reload');" id="cancel_cement_changes" />
                <input type="button" value="Save" onclick="saveCement(this.form);" id="save_cement" />
                <input type="button" value="Save as..." onclick="saveCementAs(this.form);" id="save_cement_as" />
                <input type="button" value="Delete" onclick="deleteCement(this.form);" id="delete_cement" /><span id="lab-materials-cement-save" class="help-icon"></span>
            </nested:nest>
        </div>
    </fieldset>
    <fieldset id="edit_fly_ash" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_fly_ash');">Edit or create a fly ash</a><span id="lab-materials-flyash" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="flyAsh">
				Name: 
                <nested:select property="name" onchange="onChangeFlyAsh(this);" styleClass="fly_ash-element-to-reload" styleId="fly_ash_list">
                    <option value="">New fly ash&hellip</option>
                    <nested:options name="cement_database" property="flyashs" />
                </nested:select><span id="lab-materials-flyash-name" class="help-icon"></span>
                <div id="fly_ash_specific_gravity" class="fly_ash-element-to-reload">
					Specific gravity (SG):
                    <nested:text property="specific_gravity" /><span id="lab-materials-flyash-sg" class="help-icon"></span>
                </div>
                <div id="fly_ash_psd">
                    Particle Size Distribution (PSD):
                    <nested:select property="psd" styleClass="fly_ash-element-to-reload" styleId="fly_ash_psds_list">
                        <nested:options name="cement_database" property="psds" />
                    </nested:select>
                    <span id="lab-materials-flyash-psd" class="help-icon"></span>
                </div>
                <div id="fly_ash_distribute_phases">
                    Distribute flyash phases randomly:<span id="lab-materials-flyash-distribute" class="help-icon"></span>
                </div>
                <div id="fly_ash_random_distribution_mode" class="fly_ash-element-to-reload">
                    <nested:radio property="distribute_phases_by" value="0" /> on particle basis, OR
                    <nested:radio property="distribute_phases_by" value="1" /> on pixel basis
                </div>
                <fieldset id="fly_ash_properties_description_fieldset" class="collapsed">
                    <legend class="collapsable-title collapsed"><a onclick="collapseExpand('fly_ash_properties_description_fieldset');">Fly ash properties and description</a></legend>
                    <div class="collapsable-content collapsed" id="fly_ash_properties_description">
						Enter the fraction of either particles or pixels in the flyash that belong to each phase. The difference between 1.0 and the sum of the phases in the table below will be filled with inert material.
                        <table class="list-table">
                            <thead>
                                <tr>
                                    <th>
										Phase<span id="lab-materials-flyash-table-phase" class="help-icon"></span>
                                    </th>
                                    <th>
										Fraction<span id="lab-materials-flyash-table-fraction" class="help-icon"></span>
                                    </th>
                                </tr>
                            </thead>
                            <tr>
                                <td>
									Aluminosilicate glass
                                </td>
                                <td id="fly_ash_aluminosilicate_glass_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="aluminosilicate_glass_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Calcium Aluminum Disilicate
                                </td>
                                <td id="fly_ash_calcium_aluminum_disilicate_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="calcium_aluminum_disilicate_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Tricalcium Aluminate
                                </td>
                                <td id="fly_ash_tricalcium_aluminate_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="tricalcium_aluminate_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Calcium Chloride
                                </td>
                                <td id="fly_ash_calcium_chloride_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="calcium_chloride_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Silica
                                </td>
                                <td id="fly_ash_silica_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="silica_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Anhydrite (CaSO4)
                                </td>
                                <td id="fly_ash_anhydrite_fraction" class="fly_ash-element-to-reload">
                                    <nested:text property="anhydrite_fraction" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=sum_fly_ash_vol_frac',this.form,'fly_ash-vol_frac-sum');" />
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
							Description:<span id="lab-materials-flyash-description" class="help-icon"></span><br />
                            <nested:textarea property="description" style="width:100%" rows="4" cols="40" />
                        </div>
                    </div>
                </fieldset>
                <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editLabMaterials.do?action=change_fly_ash',this.form,'fly_ash-element-to-reload');" id="cancel_fly_ash_changes" />
                <input type="button" value="Save" onclick="saveFlyAsh(this.form);" id="save_fly_ash" />
                <input type="button" value="Save as..." onclick="saveFlyAshAs(this.form);" id="save_fly_ash_as" />
                <input type="button" value="Delete" onclick="deleteFlyAsh(this.form);" id="delete_fly_ash" /><span id="lab-materials-flyash-save" class="help-icon"></span>
            </nested:nest>
        </div>
    </fieldset>
    <fieldset id="edit_slag" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_slag');">Edit or create a slag</a><span id="lab-materials-slag" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="slag">
				Name: 
                <nested:select property="name" onchange="onChangeSlag(this);" styleClass="slag-element-to-reload" styleId="slag_list">
                    <option value="">New slag&hellip</option>
                    <nested:options name="cement_database" property="slags" />
                </nested:select><span id="lab-materials-slag-name" class="help-icon"></span>
                <div id="slag_specific_gravity" class="slag-element-to-reload">
					Specific gravity (SG): <nested:text property="specific_gravity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" /><span id="lab-materials-slag-sg" class="help-icon"></span>
                </div>
				Particle Size Distribution (PSD):
                <nested:select property="psd" styleClass="slag-element-to-reload" styleId="slag_psds_list">
                    <nested:options name="cement_database" property="psds" />
                </nested:select><span id="lab-materials-slag-psd" class="help-icon"></span>
                <fieldset id="slag_properties_description_fieldset" class="collapsed">
                    <legend class="collapsable-title collapsed"><a onclick="collapseExpand('slag_properties_description_fieldset');">Slag properties and description</a><span id="lab-materials-slag-table" class="help-icon"></span></legend>
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
                                    <nested:text property="molecular_mass" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" />
                                </td>
                                <td id="slag_hp_molecular_mass" class="slag-element-to-reload">
                                    <nested:text property="hp_molecular_mass" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" />
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
                                    <nested:text property="hp_density" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_slag_characteristics',this.form,'slag-characteristic-value-to-update');" />
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
									Si per mole of slag<span id="lab-materials-slag-table-si" class="help-icon"></span>
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
									C<sub>3</sub>A per mole of slag<span id="lab-materials-slag-table-c3a" class="help-icon"></span>
                                </td>
                                <td/>
                                <td id="slag_c3a_per_mole" class="slag-element-to-reload">
                                    <nested:text property="c3a_per_mole" />
                                </td>
                            </tr>
                            <tr>
                                <td>
									Base slag reactivity<span id="lab-materials-slag-table-reactivity" class="help-icon"></span>
                                </td>
                                <td id="slag_base_slag_reactivity" class="slag-element-to-reload">
                                    <nested:text property="base_slag_reactivity" />
                                </td>
                                <td/>
                            </tr>
                        </table>
                        <div id="slag_description" class="slag-element-to-reload">
							Description:<span id="lab-materials-slag-description" class="help-icon"></span><br />
                            <nested:textarea property="description" style="width:100%" rows="6" cols="40" />
                        </div>
                    </div>
                </fieldset>
            </nested:nest>
            <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editLabMaterials.do?action=change_slag',this.form,'slag-element-to-reload');" id="cancel_slag_changes" />
            <input type="button" value="Save" onclick="saveSlag(this.form);" id="save_slag" />
            <input type="button" value="Save as..." onclick="saveSlagAs(this.form);" id="save_slag_as" />
            <input type="button" value="Delete" onclick="deleteSlag(this.form);" id="delete_slag" /><span id="lab-materials-slag-save" class="help-icon"></span>
        </div>
    </fieldset>
    <fieldset id="edit_inert_filler" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_inert_filler');">Edit or create an inert filler</a><span id="lab-materials-inert" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="inertFiller">
				Name: 
                <nested:select property="name" onchange="onChangeInertFiller(this);" styleClass="inert_filler-element-to-reload" styleId="inert_filler_list">
                    <option value="">New inert filler&hellip</option>
                    <nested:options name="cement_database" property="inert_fillers" />
                </nested:select><span id="lab-materials-inert-name" class="help-icon"></span>
                <div id="inert_filler_specific_gravity" class="inert_filler-element-to-reload">
					Specific gravity: <nested:text property="specific_gravity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_inert_filler_characteristics',this.form,'inert_filler-characteristic-value-to-update');" />
                    <span id="lab-materials-inert-sg" class="help-icon"></span></div><br/>
				Particle Size Distribution (PSD):
                <nested:select property="psd" styleClass="inert_filler-element-to-reload" styleId="inert_filler_psds_list">
                    <nested:options name="cement_database" property="psds" />
                </nested:select><span id="lab-materials-inert-psd" class="help-icon"></span>
                <div id="inert_filler_description" class="inert_filler-element-to-reload">
					Description:<br />
                    <nested:textarea property="description" style="width:100%" rows="4" cols="40" />
                </div>
                <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editLabMaterials.do?action=change_inert_filler',this.form,'inert_filler-element-to-reload');" id="cancel_inert_filler_changes" />
                <input type="button" value="Save" onclick="saveInertFiller(this.form);" id="save_inert_filler" />
                <input type="button" value="Save as..." onclick="saveInertFillerAs(this.form);" id="save_inert_filler_as" />
                <input type="button" value="Delete" onclick="deleteInertFiller(this.form);" id="delete_inert_filler" /><span id="lab-materials-inert-save" class="help-icon"></span>
            </nested:nest>
        </div>
    </fieldset>
    <fieldset id="edit_aggregate" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_aggregate');">Edit or create aggregate sources</a><span id="lab-materials-aggregate" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <fieldset id="edit_coarse_aggregate" class="collapsed">
                <legend class="collapsable-title collapsed"><a onclick="collapseExpand('edit_coarse_aggregate');">Coarse aggregate</a><span id="lab-materials-aggregate" class="help-icon"></span></legend>
                <div class="collapsable-content collapsed">
                    <nested:nest property="coarseAggregate">
				Coarse aggregate source:
                        <nested:select property="name" onchange="onChangeCoarseAggregate(this);"  styleClass="coarse_aggregate-element-to-reload" styleId="coarse_aggregate_list">
                            <option value="">New coarse aggregate&hellip</option>
                            <nested:options name="cement_database" property="coarse_aggregates" />
                        </nested:select><span id="lab-materials-coarse_aggregate-name" class="help-icon"></span>
                        <div id="coarse_aggregate_zip_file" class="coarse_aggregate-element-to-reload">
					Upload data from a ZIP file for the coarse aggregate: <html:file property="uploaded_coarse_aggregate_file" accept="zip" onchange="AIM.submit(this.form, {'onStart':startUploadCoarseAggregateCallback, 'onComplete':completeUploadCoarseAggregateCallback}); this.form.submit();" styleId="coarse_aggregate_zip_file_input"/>
                        </div>
                        <nested:hidden property="type"></nested:hidden>
                        <div id="coarse_aggregate_specific_gravity" class="coarse_aggregate-element-to-reload">
					Specific gravity: <nested:text property="specific_gravity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" />
                            <span id="lab-materials-coarse_aggregate-sg" class="help-icon"></span></div><br/>
                        <div id="coarse_aggregate_bulk_modulus" class="coarse_aggregate-element-to-reload">
					Bulk modulus: <nested:text property="bulk_modulus" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" /> GPa
                            <span id="lab-materials-coarse_aggregate-bm" class="help-icon"></span></div><br/>
                        <div id="coarse_aggregate_shear_modulus" class="coarse_aggregate-element-to-reload">
					Shear modulus: <nested:text property="shear_modulus" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" /> GPa
                            <span id="lab-materials-coarse_aggregate-sm" class="help-icon"></span></div><br/>
                        <div id="coarse_aggregate_conductivity" class="coarse_aggregate-element-to-reload">
					Conductivity: <nested:text property="conductivity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" /> GPa
                            <span id="lab-materials-coarse_aggregate-cn" class="help-icon"></span></div><br/>
                        <div id="coarse_aggregate_description" class="coarse_aggregate-element-to-reload">
					Description:<br />
                            <nested:textarea property="infString" style="width:100%" rows="4" cols="40" />
                        </div>
                        <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editLabMaterials.do?action=change_coarse_aggregate',this.form,'coarse_aggregate-element-to-reload');" id="cancel_coarse_aggregate_changes" />
                        <input type="button" value="Save" onclick="saveCoarseAggregate(this.form);" id="save_coarse_aggregate" />
                        <input type="button" value="Save as..." onclick="saveCoarseAggregateAs(this.form);" id="save_coarse_aggregate_as" />
                        <input type="button" value="Delete" onclick="deleteCoarseAggregate(this.form);" id="delete_coarse_aggregate" /><span id="lab-materials-coarse_aggregate-save" class="help-icon"></span>
                    </nested:nest>
                </div>
            </fieldset>
            <fieldset id="edit_fine_aggregate" class="collapsed">
                <legend class="collapsable-title collapsed"><a onclick="collapseExpand('edit_fine_aggregate');">Fine aggregate</a><span id="lab-materials-aggregate" class="help-icon"></span></legend>
                <div class="collapsable-content collapsed">
                    <nested:nest property="fineAggregate">
				Fine Aggregate Source:
                        <nested:select property="name" onchange="onChangeFineAggregate(this);"  styleClass="fine_aggregate-element-to-reload" styleId="fine_aggregate_list">
                            <option value="">New fine aggregate&hellip</option>
                            <nested:options name="cement_database" property="fine_aggregates" />
                        </nested:select><span id="lab-materials-fine_aggregate-name" class="help-icon"></span>
                        <div id="fine_aggregate_zip_file" class="fine_aggregate-element-to-reload">
					Upload data from a ZIP file for the fine aggregate: <html:file property="uploaded_fine_aggregate_file" accept="zip" onchange="AIM.submit(this.form, {'onStart':startUploadFineAggregateCallback, 'onComplete':completeUploadFineAggregateCallback}); this.form.submit();" styleId="fine_aggregate_zip_file_input"/>
                        </div>
                        <nested:hidden property="type"></nested:hidden>
                        <div id="fine_aggregate_specific_gravity" class="fine_aggregate-element-to-reload">
					Specific gravity (SG): <nested:text property="specific_gravity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" />
                            <span id="lab-materials-fine_aggregate-sg" class="help-icon"></span></div><br/>
                        <div id="fine_aggregate_bulk_modulus" class="fine_aggregate-element-to-reload">
					Bulk modulus: <nested:text property="bulk_modulus" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" /> GPa
                            <span id="lab-materials-fine_aggregate-bm" class="help-icon"></span></div><br/>
                        <div id="fine_aggregate_shear_modulus" class="fine_aggregate-element-to-reload">
					Shear modulus: <nested:text property="shear_modulus" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_fine_aggregate_characteristics',this.form,'fine_aggregate-characteristic-value-to-update');" /> GPa
                            <span id="lab-materials-fine_aggregate-sm" class="help-icon"></span></div><br/>
                        <div id="fine_aggregate_conductivity" class="fine_aggregate-element-to-reload">
					Conductivity: <nested:text property="conductivity" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editLabMaterials.do?action=update_coarse_aggregate_characteristics',this.form,'coarse_aggregate-characteristic-value-to-update');" /> GPa
                            <span id="lab-materials-fine_aggregate-cn" class="help-icon"></span></div><br/>
                        <div id="fine_aggregate_description" class="fine_aggregate-element-to-reload">
					Description:<br />
                            <nested:textarea property="infString" style="width:100%" rows="4" cols="40" />
                        </div>
                        <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editLabMaterials.do?action=change_fine_aggregate',this.form,'fine_aggregate-element-to-reload');" id="cancel_fine_aggregate_changes" />
                        <input type="button" value="Save" onclick="saveFineAggregate(this.form);" id="save_fine_aggregate" />
                        <input type="button" value="Save as..." onclick="saveFineAggregateAs(this.form);" id="save_fine_aggregate_as" />
                        <input type="button" value="Delete" onclick="deleteFineAggregate(this.form);" id="delete_fine_aggregate" /><span id="lab-materials-fine_aggregate-save" class="help-icon"></span>
                    </nested:nest>
                </div>
            </fieldset>
        </div>
    </fieldset>
    <fieldset id="edit_cement_data_file" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_cement_data_file');">Edit or create a cement data file</a><span id="lab-materials-datafile" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="cementDataFile">
				Name: 
                <nested:select property="name" onchange="onChangeCementDataFile(this);" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_list">
                    <option value="">New cement data file&hellip</option>
                    <nested:options name="cement_database" property="cement_data_files" />
                </nested:select><span id="lab-materials-datafile-name" class="help-icon"></span><br />
                <!-- <div id="cement_data_file_type" class="cement-data-file-to-reload">-->
                Type:
                <nested:select property="type" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_type">
                    <nested:optionsCollection name="cement_database" property="cement_data_file_types" value="key" label="value" />
                </nested:select><span id="lab-materials-datafile-type" class="help-icon"></span><!--</div>--><br />
                Data:<span id="lab-materials-datafile-data" class="help-icon"></span>
                <nested:textarea property="dataString" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_data" style="width:100%" rows="10" cols="40" />
                <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editLabMaterials.do?action=change_cement_data_file',this.form,'cement_data_file-element-to-reload');" id="cancel_cement_data_file_changes" />
                <input type="button" value="Save" onclick="saveCementDataFile(this.form);" id="save_cement_data_file" />
                <input type="button" value="Save as..." onclick="saveCementDataFileAs(this.form);" id="save_cement_data_file_as" />
                <input type="button" value="Delete" onclick="deleteDataFile(this.form);" id="delete_cement_data_file" />
            </nested:nest><span id="lab-materials-datafile-save" class="help-icon"></span>
        </div>
    </fieldset>

    <!-- <html:submit property="action" value="View" styleClass="submit-link"/>
		Create a new particle size distribution<html:submit property="action" value="New PSD" styleClass="submit-link"/>
		Create a new inert filler<html:submit property="action" value="New filler" styleClass="submit-link"/>
		Create a new file of type
    <html:select property="file_type" >
		<option>cement alkali</option>
		<option>hydration parameters</option>
		<option>temperature file</option>
		<option>fly ash alkali</option>
    </html:select>	<html:submit property="action" value="New file" styleClass="submit-link"/>
	-->
</html:form>

<!-- Tooltip Help -->
<div id="lab-materials-overview_tt" class="tooltip" style="display:none">
    <p>This page is used to take stock of the inventory of materials available in the virtual laboratory. The characteristics of each material, whether it be Portland cement or a supplementary cementitious material, can be examined in detail. Existing materials can be edited to change one or more characteristics and then saved as a new material. Likewise, altogether new materials can be added by uploading the required files collectively as a zipped archive.
    </p>
</div>
<div id="lab-materials-cement_tt" class='tooltip' style="display:none">
    <p>
		This section is for viewing, editing, or adding to the inventory of Portland cement powders in the virtual laboratory.
    </p>
</div>
<div id="lab-materials-cement-name_tt" class='tooltip' style="display:none">
    <p>
		To view or edit the characteristics of an existing Portland cement, choose its name from the pull-down menu. To add a completely new cement, choose <b>New cement ...</b> from the pull-down menu, then upload a zipped archive with all the appropriate files by clicking on the <b>Choose</b> button and selecting the zipped archive on your computer. Once the file is selected, the new properties will be available in the <b>Cement Data</b> section.
    </p>
</div>
<div id="lab-materials-cement-data_tt" class='tooltip' style="display:none">
    <p>
		The characteristics of a specified Portland cement are displayed in a number of text boxes in this section. Click on the arrow next to "Cement Data" to view or collapse these text boxes. More information on each characteristic can be found by clicking on the help icon for each one.
    </p>
</div>
<div id="lab-materials-cement-data-psd_tt" class='tooltip' style="display:none">
    <p>
        <b>PSD</b>. The particle size distribution of the powder, listed as a probability density function, i.e., the mass fraction of particles having the diameter listed in the first column.
    </p>
</div>
<div id="lab-materials-cement-data-pfc_tt" class='tooltip' style="display:none">
    <p>
        <b>PFC</b>. PFC is an acronym for "Phase Fractions of Clinker". The left column gives the volume fraction, on a total clinker volume basis, of alite (C<sub>3</sub>S), belite (C<sub>2</sub>S), aluminate (C<sub>3</sub>A), ferrite (C<sub>4</sub>AF), arcanite (K<sub>2</sub>SO<sub>4</sub>), and thaumasite (Na<sub>2</sub>SO<sub>4</sub>). The second column gives the surface area fractions of these minerals on a total clinker surface area basis.
    </p>
</div>
<div id="lab-materials-cement-data-xray_tt" class='tooltip' style="display:none">
    <p>
        <b>X-ray Diffraction</b>. This table lists the results of Quantitative
		X-ray Powder Diffraction (QXRD) using Reitveld refinement. Data are provided both on
		total solids mass basis and total solids volume basis.
    </p>
</div>
<div id="lab-materials-cement-data-sil_tt" class='tooltip' style="display:none">
    <p>
        <b>Sil</b>. This table is the isotropic two-point correlation function for silicates (alite and belite combined) in the clinker. The first column is separation distance between a silicate pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also a silicate mineral.
    </p>
</div>
<div id="lab-materials-cement-data-c3s_tt" class='tooltip' style="display:none">
    <p>
        <b>C<sub>3</sub>S</b>. This table is the isotropic two-point correlation function for alite (C<sub>3</sub>S) in the clinker. The first column is separation distance between an alite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by alite.
    </p>
</div>
<div id="lab-materials-cement-data-c4af_tt" class='tooltip' style="display:none">
    <p>
        <b>C<sub>4</sub>AF</b>. This table is the isotropic two-point correlation function for ferrite (C<sub>4</sub>AF) in the clinker. The first column is separation distance between a ferrite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by ferrite. <b>Note</b>: This table will be empty if the volume fraction of C<sub>3</sub>A in the clinker is greater than the volume fraction of C<sub>4</sub>AF.
    </p>
</div>
<div id="lab-materials-cement-data-c3a_tt" class='tooltip' style="display:none">
    <p>
        <b>C<sub>3</sub>A</b>. This table is the isotropic two-point correlation function for aluminate (C<sub>3</sub>A) in the clinker. The first column is separation distance between an aluminate pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by aluminate. <b>Note</b>: This table will be empty if the volume fraction of C<sub>3</sub>A in the clinker is less than the volume fraction of C<sub>4</sub>AF.
    </p>
</div>
<div id="lab-materials-cement-data-na2so4_tt" class='tooltip' style="display:none">
    <p>
        <b>Na<sub>2</sub>SO<sub>4</sub></b>. This table is the isotropic two-point correlation function for thaumasite (Na<sub>2</sub>SO<sub>4</sub>) in the clinker. The first column is separation distance between a thaumasite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by thaumasite. <b>Note</b>: This table will be empty if the cement was characterized prior to 2005.
    </p>
</div>
<div id="lab-materials-cement-data-k2so4_tt" class='tooltip' style="display:none">
    <p>
        <b>K<sub>2</sub>SO<sub>4</sub></b>. This table is the isotropic two-point correlation function for arcanite (K<sub>2</sub>SO<sub>4</sub>) in the clinker. The first column is separation distance between an arcanite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by arcanite. <b>Note</b>: This table will be empty if the cement was characterized prior to 2005.
    </p>
</div>
<div id="lab-materials-cement-data-alu_tt" class='tooltip' style="display:none">
    <p>
        <b>Alu</b>. This table is the isotropic two-point correlation function for combined aluminates (C<sub>3</sub>A and C<sub>4</sub>AF) in the clinker. The first column is separation distance between an aluminate/ferrite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by aluminate/ferrite. <b>Note</b>: This table will be empty if the cement was characterized prior to 2005.
    </p>
</div>
<div id="lab-materials-cement-data-sulfates_tt" class='tooltip' style="display:none">
    <p>View or edit the <b>mass</b> fractions of the three calcium sulfate carriers in Portland cement. Numbers are based on a total clinker plus calcium sulfate solids basis.
    </p>
</div>
<div id="lab-materials-cement-save_tt" class='tooltip' style="display:none">
    <ul>
        <li>Press the "Cancel" button to cancel any changes made to the characteristics of a cement.
        </li>
        <li>Press the "Save" button to save the changes made as the same cement. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new characteristics as a new cement, and then give a unique name to the new material when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected cement.
        </li>
    </ul>
</div>
<div id="lab-materials-flyash_tt" class="tooltip" style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of fly ashes in the virtual laboratory.
    </p>
</div>
<div id="lab-materials-flyash-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing fly ash, choose its name from the pull-down menu.
    </p>
</div>
<div id="lab-materials-flyash-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the fly ash, i.e., its density relative to the density of water.
    </p>
</div>
<div id="lab-materials-flyash-psd_tt" class="tooltip" style="display:none">
    <p>View or edit the particle size distribution for the fly ash powder. Currently, the different PSDs available are given by a name (associated material or other descriptive name). <b>Note</b>: The name chosen in the pull-down menu affects only the PSD of the fly ash, not its chemical composition or other characteristics.
    </p>
</div>
<div id="lab-materials-flyash-distribute_tt" class="tooltip" style="display:none">
    <p>When the fly ash is added to a mix, each fly ash particle can be assigned a single phase at random based on the volume fractions in the table below (<b>particle basis</b>). Alternatively, each particle can be composed of multiple phases proportioned according to the fractions in the table below (<b>pixel basis</b>). It is up to the user to decide, based on microscopic examination of the particles, which scenario best represents the distribution of fly ash phases.
    </p>
</div>
<div id="lab-materials-flyash-table-phase_tt" class="tooltip" style="display:none">
    <p>There are seven phases recognized by VCCTL for fly ash materials. Six of them are given in this column. The seventh phase is considered to be inert filler. Any fly ash material that has not been assigned one of the six listed phases is considered to be inert filler.
    </p>
</div>
<div id="lab-materials-flyash-table-fraction_tt" class="tooltip" style="display:none">
    <p>View or edit the <b>volume fraction</b>, on a total fly ash volume basis, for each phase in the first column. If the sum of the fractions in this column is less than 1.0, the remaning volume fraction will be assigned as inert filler.
    </p>
</div>
<div id="lab-materials-flyash-description_tt" class="tooltip" style="display:none">
    <p>View or edit a verbal description of the fly ash material. This is for user information purposes only, and does not factor into any of the calculations performed by VCCTL.
    </p>
</div>
<div id="lab-materials-flyash-save_tt" class='tooltip' style="display:none">
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
<div id="lab-materials-slag_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of ground granulated blast furnace slags (GGBS) in the virtual laboratory.
    </p>
</div>
<div id="lab-materials-slag-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing slag, choose its name from the pull-down menu.
    </p>
</div>
<div id="lab-materials-slag-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the slag, i.e., its density relative to the density of water.
    </p>
</div>
<div id="lab-materials-slag-psd_tt" class="tooltip" style="display:none">
    <p>View or edit the particle size distribution for the slag powder. Currently, the different PSDs available are given by a name (associated material or other descriptive name). <b>Note</b>: The name chosen in the pull-down menu affects only the PSD of the slag, not its chemical composition or other characteristics.
    </p>
</div>
<div id="lab-materials-slag-table_tt" class="tooltip" style="display:none">
    <p>View or edit the physicochemical properties of the slag <b>and</b> of its hydration product.
    </p>
</div>
<div id="lab-materials-slag-table-si_tt" class="tooltip" style="display:none">
    <p>
        <b>Si per mole of slag</b>. Specifies the number of moles of Si per mole of slag.
    </p>
</div>
<div id="lab-materials-slag-table-c3a_tt" class="tooltip" style="display:none">
    <p>
        <b>C<sub>3</sub>A per mole of slag</b>. Specifies the number of moles of C<sub>3</sub>A per mole of slag.
    </p>
</div>
<div id="lab-materials-slag-table-reactivity_tt" class="tooltip" style="display:none">
    <p>
        <b>Base slag reactivity</b>. This is a dimensionless, nonnegative real number that specifies how readily the slag reacts with water, relative to the default slag reactivity that is specified in the hydration parameter file. A value of 1.0 leaves the reactivity unchanged, a value of X makes the slag reactivity X times as fast as the default value.
    </p>
</div>
<div id="lab-materials-slag-description_tt" class="tooltip" style="display:none">
    <p>View or edit a verbal description of the slag material. This is for user information purposes only, and does not factor into any of the calculations performed by VCCTL.
    </p>
</div>
<div id="lab-materials-slag-save_tt" class='tooltip' style="display:none">
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
<div id="lab-materials-inert_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of inert filler in the virtual laboratory.  Inert filler
        is considered to be any solid that does not participate in hydration reactions.
    </p>
</div>
<div id="lab-materials-inert-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing inert filler, choose its name from the pull-down menu.
        To create a new inert filler, choose "New inert filler..." from the pull-down menu.
    </p>
</div>
<div id="lab-materials-inert-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the filler, i.e., its density relative to the density of water.
    </p>
</div>
<div id="lab-materials-inert-psd_tt" class="tooltip" style="display:none">
    <p>View or edit the particle size distribution for the inert filler. Currently, the different PSDs available are given by a name (associated material or other descriptive name). <b>Note</b>: The name chosen in the pull-down menu affects only the PSD of the filler, not its chemical composition or other characteristics.
    </p>
</div>
<div id="lab-materials-inert-save_tt" class='tooltip' style="display:none">
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
<div id="lab-materials-aggregate_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of coarse and fine aggregate in the virtual laboratory.
    </p>
</div>
<div id="lab-materials-coarse_aggregate-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing coarse aggregate, choose its name from the pull-down menu.
        To create a new coarse aggregate, choose "New coarse aggregate..." from the pull-down menu.
    </p>
</div>
<div id="lab-materials-coarse_aggregate-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the aggregate, i.e., its density relative to the density of water.
    </p>
</div>
<div id="lab-materials-coarse_aggregate-bm_tt" class="tooltip" style="display:none">
    <p>View or edit the bulk modulus, K, of the aggregate.
    </p>
</div>
<div id="lab-materials-coarse_aggregate-sm_tt" class="tooltip" style="display:none">
    <p>View or edit the shear modulus, G, of the aggregate.
    </p>
</div>
<div id="lab-materials-coarse_aggregate-save_tt" class='tooltip' style="display:none">
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
<div id="lab-materials-fine_aggregate-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing fine aggregate, choose its name from the pull-down menu.
        To create a new fine aggregate, choose "New fine aggregate..." from the pull-down menu.
    </p>
</div>
<div id="lab-materials-fine_aggregate-sg_tt" class="tooltip" style="display:none">
    <p>View or edit the overall specific gravity of the aggregate, i.e., its density relative to the density of water.
    </p>
</div>
<div id="lab-materials-fine_aggregate-bm_tt" class="tooltip" style="display:none">
    <p>View or edit the bulk modulus, K, of the aggregate.
    </p>
</div>
<div id="lab-materials-fine_aggregate-sm_tt" class="tooltip" style="display:none">
    <p>View or edit the shear modulus, G, of the aggregate.
    </p>
</div>
<div id="lab-materials-fine_aggregate-save_tt" class='tooltip' style="display:none">
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
<div id="lab-materials-datafile_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of data files related to
        cementitious materials.  The kinds of data files accessible here are particle size
        distribution (PSD), alkali characteristics, isothermal calorimetry, and chemical
        shrinkage.
    </p>
</div>
<div id="lab-materials-datafile-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing data file, choose its name from
        this pull-down menu.  To create a new data file, choose "New cement data file..."
        from the pull-down menu, and then select its type from the next menu.
    </p>
</div>
<div id="lab-materials-datafile-type_tt" class="tooltip" style="display:none">
    <p>Specifies the type of data file selected.  This will be automatically chosen
        for any existing data file, but you will need to specify it yourself for a new
        data file.
    </p>
</div>
<div id="lab-materials-datafile-data_tt" class="tooltip" style="display:none">
    <p>View or edit the data contained in the data file.  For existing files, the data appear
        in the window below.  For new files, you will need to type in the data or cut-and-paste
        the data from another file.
    </p>
</div>
<div id="lab-materials-datafile-save_tt" class='tooltip' style="display:none">
    <ol>
        <li>Press the "Cancel" button to cancel any changes made to the data file.
        </li>
        <li>Press the "Save" button to save the changes made as the same datafile. <b>Note</b>: The previous characteristics will be overwritten and lost if the "Save" button is pressed.
        </li>
        <li>Press the "Save as..." button to save the new data file, and then give a unique name to the data when prompted.
        </li>
        <li>Press the "Delete" button to delete the selected data file.
        </li>
    </ol>
</div>
<!-- End of Tooltip Help -->
<script type="text/javascript">
    Tooltip.autoMoveToCursor = true;
    Tooltip.add("lab-materials-overview", "lab-materials-overview_tt");
    Tooltip.add("lab-materials-cement", "lab-materials-cement_tt");
    Tooltip.add("lab-materials-cement-name", "lab-materials-cement-name_tt");
    Tooltip.add("lab-materials-cement-data", "lab-materials-cement-data_tt");
    Tooltip.add("lab-materials-cement-data-psd", "lab-materials-cement-data-psd_tt");
    Tooltip.add("lab-materials-cement-data-pfc", "lab-materials-cement-data-pfc_tt");
    Tooltip.add("lab-materials-cement-data-xray", "lab-materials-cement-data-xray_tt");
    Tooltip.add("lab-materials-cement-data-sil", "lab-materials-cement-data-sil_tt");
    Tooltip.add("lab-materials-cement-data-c3s", "lab-materials-cement-data-c3s_tt");
    Tooltip.add("lab-materials-cement-data-c4af", "lab-materials-cement-data-c4af_tt");
    Tooltip.add("lab-materials-cement-data-c3a", "lab-materials-cement-data-c3a_tt");
    Tooltip.add("lab-materials-cement-data-na2so4", "lab-materials-cement-data-na2so4_tt");
    Tooltip.add("lab-materials-cement-data-k2so4", "lab-materials-cement-data-k2so4_tt");
    Tooltip.add("lab-materials-cement-data-alu", "lab-materials-cement-data-alu_tt");
    Tooltip.add("lab-materials-cement-data-sulfates", "lab-materials-cement-data-sulfates_tt");
    Tooltip.add("lab-materials-cement-save", "lab-materials-cement-save_tt");
    Tooltip.add("lab-materials-flyash", "lab-materials-flyash_tt");
    Tooltip.add("lab-materials-flyash-name", "lab-materials-flyash-name_tt");
    Tooltip.add("lab-materials-flyash-sg", "lab-materials-flyash-sg_tt");
    Tooltip.add("lab-materials-flyash-psd", "lab-materials-flyash-psd_tt");
    Tooltip.add("lab-materials-flyash-distribute", "lab-materials-flyash-distribute_tt");
    Tooltip.add("lab-materials-flyash-table-phase", "lab-materials-flyash-table-phase_tt");
    Tooltip.add("lab-materials-flyash-table-fraction", "lab-materials-flyash-table-fraction_tt");
    Tooltip.add("lab-materials-flyash-description", "lab-materials-flyash-description_tt");
    Tooltip.add("lab-materials-flyash-save", "lab-materials-flyash-save_tt");
    Tooltip.add("lab-materials-slag", "lab-materials-slag_tt");
    Tooltip.add("lab-materials-slag-name", "lab-materials-slag-name_tt");
    Tooltip.add("lab-materials-slag-sg", "lab-materials-slag-sg_tt");
    Tooltip.add("lab-materials-slag-psd", "lab-materials-slag-psd_tt");
    Tooltip.add("lab-materials-slag-table", "lab-materials-slag-table_tt");
    Tooltip.add("lab-materials-slag-table-si", "lab-materials-slag-table-si_tt");
    Tooltip.add("lab-materials-slag-table-c3a", "lab-materials-slag-table-c3a_tt");
    Tooltip.add("lab-materials-slag-table-reactivity", "lab-materials-slag-table-reactivity_tt");
    Tooltip.add("lab-materials-slag-description", "lab-materials-slag-description_tt");
    Tooltip.add("lab-materials-slag-save", "lab-materials-slag-save_tt");
    Tooltip.add("lab-materials-inert", "lab-materials-inert_tt");
    Tooltip.add("lab-materials-inert-name", "lab-materials-inert-name_tt");
    Tooltip.add("lab-materials-inert-sg", "lab-materials-inert-sg_tt");
    Tooltip.add("lab-materials-inert-psd", "lab-materials-inert-psd_tt");
    Tooltip.add("lab-materials-inert-save", "lab-materials-inert-save_tt");
    Tooltip.add("lab-materials-aggregate", "lab-materials-aggregate_tt");
    Tooltip.add("lab-materials-coarse_aggregate-name", "lab-materials-coarse_aggregate-name_tt");
    Tooltip.add("lab-materials-coarse_aggregate-sg", "lab-materials-coarse_aggregate-sg_tt");
    Tooltip.add("lab-materials-coarse_aggregate-bm", "lab-materials-coarse_aggregate-bm_tt");
    Tooltip.add("lab-materials-coarse_aggregate-sm", "lab-materials-coarse_aggregate-sm_tt");
    Tooltip.add("lab-materials-coarse_aggregate-psd", "lab-materials-coarse_aggregate-psd_tt");
    Tooltip.add("lab-materials-coarse_aggregate-save", "lab-materials-coarse_aggregate-save_tt");
    Tooltip.add("lab-materials-fine_aggregate-name", "lab-materials-fine_aggregate-name_tt");
    Tooltip.add("lab-materials-fine_aggregate-sg", "lab-materials-fine_aggregate-sg_tt");
    Tooltip.add("lab-materials-fine_aggregate-bm", "lab-materials-fine_aggregate-bm_tt");
    Tooltip.add("lab-materials-fine_aggregate-sm", "lab-materials-fine_aggregate-sm_tt");
    Tooltip.add("lab-materials-fine_aggregate-psd", "lab-materials-fine_aggregate-psd_tt");
    Tooltip.add("lab-materials-fine_aggregate-save", "lab-materials-fine_aggregate-save_tt");
    Tooltip.add("lab-materials-datafile", "lab-materials-datafile_tt");
    Tooltip.add("lab-materials-datafile-name", "lab-materials-datafile-name_tt");
    Tooltip.add("lab-materials-datafile-type", "lab-materials-datafile-type_tt");
    Tooltip.add("lab-materials-datafile-data", "lab-materials-datafile-data_tt");
    Tooltip.add("lab-materials-datafile-save", "lab-materials-datafile-save_tt");
</script>
