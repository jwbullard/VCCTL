<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<fieldset>
	<legend>Thermal</legend>
	Conditions: 
	<div id="thermal_conditions" class="to-reload radio-buttons-group">
		<html:radio property="thermal_conditions" value="isothermal" onclick="onChangeThermalConditions(this);" /> isothermal<br/>
		<html:radio property="thermal_conditions" value="semi-adiabatic" onclick="onChangeThermalConditions(this);" /> semi-adiabatic<br/>
		<html:radio property="thermal_conditions" value="adiabatic" onclick="onChangeThermalConditions(this);" /> adiabatic<br/>
	</div>
	<div id="initial_temperature" class="to-reload">
		Initial temperature: 
		<html:text property="initial_temperature" size="4" onchange="onChangeInitialTemperature(this);" /> &deg;C
	</div>
	<logic:equal name="hydrationForm" property="thermal_conditions" value="semi-adiabatic">
		<div id="ambient_temperature" class="to-reload">
	</logic:equal>
	<logic:notEqual name="hydrationForm" property="thermal_conditions" value="semi-adiabatic">
		<div id="ambient_temperature" class="hidden to-reload">
	</logic:notEqual>
			Ambient temperature: 
			<html:text property="ambient_temperature" size="4" /> &deg;C
		</div>
	<logic:equal name="hydrationForm" property="thermal_conditions" value="semi-adiabatic">
		<div id="heat_transfer_coefficient" class="to-reload">
	</logic:equal>
	<logic:notEqual name="hydrationForm" property="thermal_conditions" value="semi-adiabatic">
		<div id="heat_transfer_coefficient" class="hidden to-reload">
	</logic:notEqual>
			Heat transfer coefficient:
			<html:text property="heat_transfer_coefficient" size="4"/>
		</div>
	<logic:equal name="hydrationForm" property="has_aggregate" value="true">
		<fieldset id="aggregate-properties-fieldset" class="collapsed to-reload">
	</logic:equal>
	<logic:equal name="hydrationForm" property="has_aggregate" value="false">
		<fieldset id="aggregate-properties-fieldset" class="collapsed to-reload hidden">
	</logic:equal>
			<legend class="collapsable-title collapsed" id="aggregate-properties-title"><a onclick="collapseExpand('aggregate-properties-fieldset');">Aggregate</a></legend>
			<div class="collapsable-content collapsed" id="aggregate-properties-content">
				Initial temperature of aggregate:
				<html:text property="aggregate_initial_temperature" size="5"/> &deg;C
				Heat transfer coefficient:
				<html:text property="aggregate_heat_transfer_coefficient" size="5"/> W/g/&deg;C
			</div>
		</fieldset>
</fieldset>
<fieldset>
    <legend>Aging <span id="hydrate-mix-aging" class="help-icon"></span></legend>
    <div id="days_hydration_time">
        Hydrate for <html:text property="days_hydration_time" size="6" /> days
    </div>
    <div id="hydration_degree" class="slider">
		<span class="slider-label">&#133 Or stop at degree of hydration: </span>
		<div id="terminate_degree-track" class="slider-track">
			<div id="terminate_degree-handle" class="slider-handle"></div>
		</div>
        <span id="terminate_degree" class="to-reload">
            <html:text property="terminate_degree" size="3" onchange="onChangeSliderValue(this);" />
        </span>
    </div>
	<div id="aging-time_conversion_factor_mode">
		<html:radio property="aging_mode" value="time" onclick="changeAgingMode(this);" /> Use time conversion <br/>
		<logic:equal name="hydrationForm" property="aging_mode" value="time">
			<div id="aging-time_conversion_factor_mode_parameters">
		</logic:equal>
		<logic:notEqual name="hydrationForm" property="aging_mode" value="time">
			<div id="aging-time_conversion_factor_mode_parameters" style="display:none">
		</logic:notEqual>
			    <div id="time_conversion_factor">
			        Time conversion factor <html:text property="time_conversion_factor" size="6" /> h/cycle<SUP>2</SUP>
			    </div>
			</div>
	</div>
	<div id="aging-colorimetry_mode">
		<html:radio property="aging_mode" value="calorimetry" onclick="changeAgingMode(this);" /> Use a calorimetry file<br/>
		<logic:equal name="hydrationForm" property="aging_mode" value="calorimetry">
			<div id="aging-colorimetry_mode_parameters">
		</logic:equal>
		<logic:notEqual name="hydrationForm" property="aging_mode" value="calorimetry">
			<div id="aging-colorimetry_mode_parameters" style="display:none">
		</logic:notEqual>
				<div id="colorimetry_file">
					Calorimetry file: 
					<html:select property="calorimetry_file" onchange="changeCalorimetryFile(this.form);">
						<html:options name="cement_database" property="calorimetry_files"  />
					</html:select>
				</div>
				<div id="colorimetry_file_temperature">
					Temperature: <html:text property="calorimetry_temperature" size="6" />
				</div>
			</div>
	</div>
	<div id="aging-chemical_shrinkage_mode">
		<html:radio property="aging_mode" value="chemical_shrinkage" onclick="changeAgingMode(this);" /> Use a chemical shrinkage file<br/>
		<logic:equal name="hydrationForm" property="aging_mode" value="chemical_shrinkage">
			<div id="aging-chemical_shrinkage_mode_parameters">
		</logic:equal>
		<logic:notEqual name="hydrationForm" property="aging_mode" value="chemical_shrinkage">
			<div id="aging-chemical_shrinkage_mode_parameters" style="display:none">
		</logic:notEqual>
				<div id="chemical_shrinkage_file">
					Calorimetry file: 
					<html:select property="chemical_shrinkage_file">
						<html:options name="cement_database" property="chemical_shrinkage_files" />
					</html:select>
				</div>
				<div id="chemical_shrinkage_file_temperature">
					Temperature: <html:text property="chemical_shrinkage_temperature" size="6" />
				</div>
			</div>
	</div>
</fieldset>
<fieldset>
	<legend>Saturation conditions <span id="hydrate-mix-saturation-conditions" class="help-icon"></span></legend>
	<div id="saturation_conditions" class="to-reload radio-buttons-group">
		<html:radio property="saturation_conditions" value="saturated" onclick="onChangeThermalConditions(this);" /> saturated<br/>
		<html:radio property="saturation_conditions" value="sealed" onclick="onChangeThermalConditions(this);" /> sealed<br/>
	</div>
</fieldset>
<script type="text/javascript">
createSliderAssociatedWithField(document.forms[0].terminate_degree,0,1,0.01,1);
</script>