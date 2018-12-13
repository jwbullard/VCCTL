<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-nested" prefix="nested" %>

<%@page import="nist.bfrl.vcctl.database.*" %>
<%@page import="nist.bfrl.vcctl.util.Constants" %>
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
    selectSubTab(0);
</script>

<h3>Cement Materials Inventory</h3>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<html:form action="/lab-materials/editCementMaterials.do" method="POST" enctype="multipart/form-data">
    <fieldset id="edit_cement" class="expanded">
        <legend class="collapsable-title expanded"><a onclick="collapseExpand('edit_cement');"><b>Edit or create a cement</b></a><span id="cement-materials-cement" class="help-icon"></span></legend>
        <div class="collapsable-content expanded">
            <nested:nest property="cement">
				Name:
                <nested:select property="name" onchange="onChangeCement(this);" styleClass="cement-element-to-reload" styleId="cement_list" >
                    <option value="">New cement&hellip</option>
                    <nested:options name="cement_database" property="cements" />
                </nested:select><span id="cement-materials-cement-name" class="help-icon"></span>
                <br/>
                <input type="hidden" name="action" />
                <div id="cement_zip_file" class="cement-element-to-reload">
					Upload data from a ZIP file for the cement: <html:file property="uploaded_file" accept="zip" onchange="AIM.submit(this.form, {'onStart':startUploadCallback, 'onComplete':completeUploadCallback}); this.form.submit();" styleId="cement_zip_file_input"/>
                </div>
                <fieldset id="cement_image" class="cement-element-to-reload">
                    <legend><b>Segmented SEM image</b><span id="cement-materials-cement-image" class="help-icon"></span></legend>
                    <table style="width:45%; float: left;">
                        <tr>
                            <td><img src="/vcctl/image/${cemName}.gif" width="256" alt="No image available" /></td>
                        </tr>
                    </table>
                        <table style="width:45%; float: right;">
                        <tr>
                            <td>C<sub>3</sub>S</td><td>C<sub>2</sub>S</td><td>C<sub>3</sub>A</td><td>C<sub>4</sub>AF</td>
                        </tr><tr>
                            <td><img src="/vcctl/image/c3s.gif" /></td>
                            <td><img src="/vcctl/image/c2s.gif" /></td>
		            <td><img src="/vcctl/image/c3a.gif" /></td>
                            <td><img src="/vcctl/image/c4af.gif" /></td>
                        </tr><tr>
                            <td></td><td></td><td></td><td></td>
                        </tr>
                        <td>K<sub>2</sub>SO<sub>4</sub></td><td>Na<sub>2</sub>SO<sub>4</sub></td><td>Gypsum</td><td>CaCO<sub>3</sub></td>
                        </tr><tr>
                            <td><img src="/vcctl/image/k2so4.gif" /></td>
		            <td><img src="/vcctl/image/na2so4.gif" /></td>
                            <td><img src="/vcctl/image/gypsum.gif" /></td>
                            <td><img src="/vcctl/image/caco3.gif" /></td>
                        </tr><tr>
                            <td></td><td></td><td></td><td></td>
                        </tr><tr>
                            <td>SiO<sub>2</sub></td><td>Slag</td><td>Pore</td><td></td>
                        </tr><tr>
		            <td><img src="/vcctl/image/sfume.gif" /></td>
                            <td><img src="/vcctl/image/slag.gif" /></td>
                            <td><img src="/vcctl/image/emptyp.gif" /></td>
		            <td></td>
                        </tr>
                    </table>
                </fieldset>
                <fieldset id="cement_image" class="cement-element-to-reload">
                    <nested:textarea property="infString" rows="6" cols="80" styleId="cement_general_information" styleClass="cement-element-to-reload" />
                </fieldset>
                <fieldset id="cement_data_fieldset" class="collapsed">
                    <legend class="collapsable-title collapsed"><a onclick="collapseExpand('cement_data_fieldset');"><b>Cement data</b></a><span id="cement-materials-cement-data" class="help-icon"></span></legend>
                    <div class="collapsable-content collapsed" id="cement_data">
                        PSD: <span id="cement-materials-cement-data-psd" class="help-icon"></span>
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
                                <th>PFC<span id="cement-materials-cement-data-pfc" class="help-icon"></span></th>
                                <th>X-ray Diffraction Data<span id="cement-materials-cement-data-xray" class="help-icon"></span></th>
                            </tr>
                            <tr>
                                <td><nested:textarea property="pfcString" rows="10" cols="14" styleId="cement_pfc" styleClass="cement-element-to-reload" /></td>
                                <td><nested:textarea property="xrdString" rows="10" cols="46" styleId="cement_xray_diffraction_data" styleClass="cement-element-to-reload" /></td>
                            </tr>
                        </table>
                        <table>
                            <tr>
                                <th>Sil<span id="cement-materials-cement-data-sil" class="help-icon"></span></th>
                                <th>C<sub>3</sub>S<span id="cement-materials-cement-data-c3s" class="help-icon"></span></th>
                                <th>C<sub>4</sub>AF<span id="cement-materials-cement-data-c4af" class="help-icon"></span></th>
                                <th>C<sub>3</sub>A<span id="cement-materials-cement-data-c3a" class="help-icon"></span></th>
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
                                <th>Na<sub>2</sub>SO<sub>4</sub><span id="cement-materials-cement-data-na2so4" class="help-icon"></span></th>
                                <th>K<sub>2</sub>SO<sub>4</sub><span id="cement-materials-cement-data-k2so4" class="help-icon"></span></th>
                                <th>Alu<span id="cement-materials-cement-data-alu" class="help-icon"></span></th>
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
                    <legend><b>Mass fractions of sulfates</b><span id="cement-materials-cement-data-sulfates" class="help-icon"></span></legend>
					Dihydrate
                    <nested:text property="dihyd" size="8" styleId="cement_dihydrate" />
					Hemihydrate
                    <nested:text property="hemihyd" size="8" styleId="cement_hemihydrate" />
					Anhydrite
                    <nested:text property="anhyd" size="8" styleId="cement_anhydrite" />
                </fieldset>
                <input type="button" value="Cancel" onclick="ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=change_cement',this.form,'cement-element-to-reload');" id="cancel_cement_changes" />
                <input type="button" value="Save" onclick="saveCement(this.form);" id="save_cement" />
                <input type="button" value="Save as..." onclick="saveCementAs(this.form);" id="save_cement_as" />
                <input type="button" value="Delete" onclick="deleteCement(this.form);" id="delete_cement" /><span id="cement-materials-cement-save" class="help-icon"></span>
            </nested:nest>
        </div>
    </fieldset>
    <fieldset id="edit_cement_data_file" class="collapsed">
        <legend class="collapsable-title collapsed"><a onclick="collapseExpand('edit_cement_data_file');"><b>Edit or create a cement data file</b></a><span id="cement-materials-datafile" class="help-icon"></span></legend>
        <div class="collapsable-content collapsed">
            <nested:nest property="cementDataFile">
				Name:
                <nested:select property="name" onchange="onChangeCementDataFile(this);" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_list">
                    <option value="">New cement data file&hellip</option>
                    <nested:options name="cement_database" property="cement_data_files" />
                </nested:select><span id="cement-materials-datafile-name" class="help-icon"></span><br />
                <!-- <div id="cement_data_file_type" class="cement-data-file-to-reload">-->
                Type:
                <nested:select property="type" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_type">
                    <%-- <nested:optionsCollection name="cement_database" property="cement_data_file_types" value="key" label="value" /> --%>
                    <nested:options name="cement_database" property="cement_data_file_types" />
                </nested:select><span id="cement-materials-datafile-type" class="help-icon"></span><!--</div>--><br />
                <table>
                    <tr>
                        <th>Data Content</th>
                        <th>Data Information</th>
                    </tr>
                    <tr>
                        <td><nested:textarea property="dataString" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_data" style="width:95%" rows="10" cols="30" onchange="checkCementData(this.form);" /></td>
                        <td><nested:textarea property="infString" styleClass="cement_data_file-element-to-reload" styleId="cement_data_file_inf" style="width:95%" rows="10" cols="30" /></td>
                    </tr>
                </table>
                <input type="button" value="Cancel" onclick="retrieveURL('/vcctl/lab-materials/editCementMaterials.do?action=change_cement_data_file',this.form,'cement_data_file-element-to-reload');" id="cancel_cement_data_file_changes" />
                <input type="button" value="Save" onclick="saveCementDataFile(this.form);" id="save_cement_data_file" />
                <input type="button" value="Save as..." onclick="saveCementDataFileAs(this.form);" id="save_cement_data_file_as" />
                <input type="button" value="Delete" onclick="deleteDataFile(this.form);" id="delete_cement_data_file" />
            </nested:nest><span id="cement-materials-datafile-save" class="help-icon"></span>
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
<div id="cement-materials-cement_tt" class='tooltip' style="display:none">
    <p>
		This section is for viewing, editing, or adding to the inventory of Portland cement powders in the virtual laboratory.
    </p>
</div>
<div id="cement-materials-cement-name_tt" class='tooltip' style="display:none">
    <p>
		To view or edit the characteristics of an existing Portland cement, choose its name from the pull-down menu. To add a completely new cement, choose <b>New cement ...</b> from the pull-down menu, then upload a zipped archive with all the appropriate files by clicking on the <b>Choose</b> button and selecting the zipped archive on your computer. Once the file is selected, the new properties will be available in the <b>Cement Data</b> section.
    </p>
</div>
<div id="cement-materials-cement-image_tt" class='tooltip' style="display:none">
    <p>
		The image displayed here is a false color micrograph image produced by a combination of scanning electron backscattered electron imaging and X-ray dot mapping.  The image is not editable, unlike most of the other fields.
    </p>
</div>
<div id="cement-materials-cement-data_tt" class='tooltip' style="display:none">
    <p>
		The characteristics of a specified Portland cement are displayed in a number of text boxes in this section. Click on the arrow next to "Cement Data" to view or collapse these text boxes. More information on each characteristic can be found by clicking on the help icon for each one.
    </p>
</div>
<div id="cement-materials-cement-data-psd_tt" class='tooltip' style="display:none">
    <p>
        <b>PSD</b>. The particle size distribution of the powder, listed as a probability density function, i.e., the mass fraction of particles having the diameter listed in the first column.
    </p>
</div>
<div id="cement-materials-cement-data-pfc_tt" class='tooltip' style="display:none">
    <p>
        <b>PFC</b>. PFC is an acronym for "Phase Fractions of Clinker". The left column gives the volume fraction, on a total clinker volume basis, of alite (C<sub>3</sub>S), belite (C<sub>2</sub>S), aluminate (C<sub>3</sub>A), ferrite (C<sub>4</sub>AF), arcanite (K<sub>2</sub>SO<sub>4</sub>), and thenardite (Na<sub>2</sub>SO<sub>4</sub>). The second column gives the surface area fractions of these minerals on a total clinker surface area basis.
    </p>
</div>
<div id="cement-materials-cement-data-xray_tt" class='tooltip' style="display:none">
    <p>
        <b>X-ray Diffraction</b>. This table lists the results of Quantitative
		X-ray Powder Diffraction (QXRD) using Reitveld refinement. Data are provided both on
		total solids mass basis and total solids volume basis.
    </p>
</div>
<div id="cement-materials-cement-data-sil_tt" class='tooltip' style="display:none">
    <p>
        <b>Sil</b>. This table is the isotropic two-point correlation function for silicates (alite and belite combined) in the clinker. The first column is separation distance between a silicate pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also a silicate mineral.
    </p>
</div>
<div id="cement-materials-cement-data-c3s_tt" class='tooltip' style="display:none">
    <p>
        <b>C<sub>3</sub>S</b>. This table is the isotropic two-point correlation function for alite (C<sub>3</sub>S) in the clinker. The first column is separation distance between an alite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by alite.
    </p>
</div>
<div id="cement-materials-cement-data-c4af_tt" class='tooltip' style="display:none">
    <p>
        <b>C<sub>4</sub>AF</b>. This table is the isotropic two-point correlation function for ferrite (C<sub>4</sub>AF) in the clinker. The first column is separation distance between a ferrite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by ferrite. <b>Note</b>: This table will be empty if the volume fraction of C<sub>3</sub>A in the clinker is greater than the volume fraction of C<sub>4</sub>AF.
    </p>
</div>
<div id="cement-materials-cement-data-c3a_tt" class='tooltip' style="display:none">
    <p>
        <b>C<sub>3</sub>A</b>. This table is the isotropic two-point correlation function for aluminate (C<sub>3</sub>A) in the clinker. The first column is separation distance between an aluminate pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by aluminate. <b>Note</b>: This table will be empty if the volume fraction of C<sub>3</sub>A in the clinker is less than the volume fraction of C<sub>4</sub>AF.
    </p>
</div>
<div id="cement-materials-cement-data-na2so4_tt" class='tooltip' style="display:none">
    <p>
        <b>Na<sub>2</sub>SO<sub>4</sub></b>. This table is the isotropic two-point correlation function for thaumasite (Na<sub>2</sub>SO<sub>4</sub>) in the clinker. The first column is separation distance between a thaumasite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by thaumasite. <b>Note</b>: This table will be empty if the cement was characterized prior to 2005.
    </p>
</div>
<div id="cement-materials-cement-data-k2so4_tt" class='tooltip' style="display:none">
    <p>
        <b>K<sub>2</sub>SO<sub>4</sub></b>. This table is the isotropic two-point correlation function for arcanite (K<sub>2</sub>SO<sub>4</sub>) in the clinker. The first column is separation distance between an arcanite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by arcanite. <b>Note</b>: This table will be empty if the cement was characterized prior to 2005.
    </p>
</div>
<div id="cement-materials-cement-data-alu_tt" class='tooltip' style="display:none">
    <p>
        <b>Alu</b>. This table is the isotropic two-point correlation function for combined aluminates (C<sub>3</sub>A and C<sub>4</sub>AF) in the clinker. The first column is separation distance between an aluminate/ferrite pixel and a randomly chosen pixel in the segmented microstructure image, and the second column is the probability that the randomly chosen pixel is also occupied by aluminate/ferrite. <b>Note</b>: This table will be empty if the cement was characterized prior to 2005.
    </p>
</div>
<div id="cement-materials-cement-data-sulfates_tt" class='tooltip' style="display:none">
    <p>View or edit the <b>mass</b> fractions of the three calcium sulfate carriers in Portland cement. Numbers are based on a total clinker plus calcium sulfate solids basis.
    </p>
</div>
<div id="cement-materials-cement-save_tt" class='tooltip' style="display:none">
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
<div id="cement-materials-datafile_tt" class='tooltip' style="display:none">
    <p>This section is for viewing, editing, or adding to the inventory of data files related to
        cementitious materials.  The kinds of data files accessible here are particle size
        distribution (PSD), alkali characteristics, isothermal calorimetry, and chemical
        shrinkage.
    </p>
</div>
<div id="cement-materials-datafile-name_tt" class="tooltip" style="display:none">
    <p>To view or edit the characteristics of an existing data file, choose its name from
        this pull-down menu.  To create a new data file, choose "New cement data file..."
        from the pull-down menu, and then select its type from the next menu.
    </p>
</div>
<div id="cement-materials-datafile-type_tt" class="tooltip" style="display:none">
    <p>Specifies the type of data file selected.  This will be automatically chosen
        for any existing data file, but you will need to specify it yourself for a new
        data file.
    </p>
</div>
<div id="cement-materials-datafile-data_tt" class="tooltip" style="display:none">
    <p>View or edit the data contained in the data file.  For existing files, the data appear
        in the window below.  For new files, you will need to type in the data or cut-and-paste
        the data from another file.
    </p>
</div>
<div id="cement-materials-datafile-save_tt" class='tooltip' style="display:none">
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
    Tooltip.add("cement-materials-cement", "cement-materials-cement_tt");
    Tooltip.add("cement-materials-cement-name", "cement-materials-cement-name_tt");
    Tooltip.add("cement-materials-cement-image", "cement-materials-cement-image_tt");
    Tooltip.add("cement-materials-cement-data", "cement-materials-cement-data_tt");
    Tooltip.add("cement-materials-cement-data-psd", "cement-materials-cement-data-psd_tt");
    Tooltip.add("cement-materials-cement-data-pfc", "cement-materials-cement-data-pfc_tt");
    Tooltip.add("cement-materials-cement-data-xray", "cement-materials-cement-data-xray_tt");
    Tooltip.add("cement-materials-cement-data-sil", "cement-materials-cement-data-sil_tt");
    Tooltip.add("cement-materials-cement-data-c3s", "cement-materials-cement-data-c3s_tt");
    Tooltip.add("cement-materials-cement-data-c4af", "cement-materials-cement-data-c4af_tt");
    Tooltip.add("cement-materials-cement-data-c3a", "cement-materials-cement-data-c3a_tt");
    Tooltip.add("cement-materials-cement-data-na2so4", "cement-materials-cement-data-na2so4_tt");
    Tooltip.add("cement-materials-cement-data-k2so4", "cement-materials-cement-data-k2so4_tt");
    Tooltip.add("cement-materials-cement-data-alu", "cement-materials-cement-data-alu_tt");
    Tooltip.add("cement-materials-cement-data-sulfates", "cement-materials-cement-data-sulfates_tt");
    Tooltip.add("cement-materials-cement-save", "cement-materials-cement-save_tt");
    Tooltip.add("cement-materials-datafile", "cement-materials-datafile_tt");
    Tooltip.add("cement-materials-datafile-name", "cement-materials-datafile-name_tt");
    Tooltip.add("cement-materials-datafile-type", "cement-materials-datafile-type_tt");
    Tooltip.add("cement-materials-datafile-data", "cement-materials-datafile-data_tt");
    Tooltip.add("cement-materials-datafile-save", "cement-materials-datafile-save_tt");
</script>
