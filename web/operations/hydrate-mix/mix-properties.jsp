<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<div id="microstructure" class="to-reload">
	Choose a mix: 
	<html:select property="microstructure" onchange="ajaxUpdateElementsWithStrutsAction('/vcctl/operation/hydrateMix.do?action=change_mix',this.form,'to-reload')">
		<html:options property="user_mix_list" />
	</html:select>
</div>
<div id="reactions-activation-energies" class="collapsable-element">
	<div id="reactions-activation-energies-title" class="collapsable-title collapsed"><a onclick="collapseExpand('reactions-activation-energies');">Reaction activation energies</a></div>
	<div id="reactions-activation-energies-content" class="collapsable-content collapsed box-content">
		<div id="cement_hydration_activation_energy" class="to-reload">
			Cement hydration:
			<html:text property="cement_hydration_activation_energy" size="5"/> kJ/mole
		</div>
		<div id="pozzolanic_reactions_activation_energy" class="to-reload">
			Pozzolanic reactions:
			<html:text property="pozzolanic_reactions_activation_energy" size="5"/> kJ/mole
		</div>
		<div id="slag_reactions_activation_energy" class="to-reload">
			Slag reactions:
			<html:text property="slag_reactions_activation_energy" size="5"/> kJ/mole
		</div>
	</div>
</div>
<div id="hydration-behavior-options" class="collapsable-element">
	<div id="hydration-behavior-options-title" class="collapsable-title collapsed"><a onclick="collapseExpand('hydration-behavior-options');">Hydration behavior options</a></div>
	<div id="hydration-behavior-options-content" class="collapsable-content collapsed box-content">
		<div id="alkali_characteristics_cement_file" class="to-reload">
			Alkali characteristics file for cement:
			<html:select property="alkali_characteristics_cement_file">
				<html:options name="cement_database" property="alkali_characteristics_files" />
			</html:select>
		</div>
		<logic:equal name="hydrationForm" property="has_fly_ash" value="true">
			<div id="alkali_characteristics_fly_ash_file" class="to-reload">
		</logic:equal>
		<logic:equal name="hydrationForm" property="has_fly_ash" value="false">
			<div id="alkali_characteristics_fly_ash_file" class="hidden to-reload">
		</logic:equal>
				Alkali characteristics file for fly ash:
				<html:select property="alkali_characteristics_fly_ash_file">
					<html:options name="cement_database" property="alkali_characteristics_files" />
				</html:select>
			</div>
		<logic:equal name="hydrationForm" property="has_slag" value="true">
			<div id="slag_characteristics_file" class="to-reload">
		</logic:equal>
		<logic:equal name="hydrationForm" property="has_slag" value="false">
			<div id="slag_characteristics_file" class="hidden to-reload">
		</logic:equal>
				Slag characteristics file:
				<html:select property="slag_characteristics_file">
					<html:options name="cement_database" property="slag_characteristics_files" />
				</html:select>
			</div>
		<logic:equal name="hydrationForm" property="has_slag_or_fly_ash_or_silica_fume" value="true">
			<div id="csh_conversion" class="to-reload">
		</logic:equal>
		<logic:equal name="hydrationForm" property="has_slag_or_fly_ash_or_silica_fume" value="false">
			<div id="csh_conversion" class="hidden to-reload">
		</logic:equal>
				Conversion of primary C-S-H to pozzolanic:
				<div class="radio-buttons-group">
					<html:radio property="csh_conversion" value="prohibited" /> prohibited<br/>
					<html:radio property="csh_conversion" value="allowed" /> allowed<br/>
				</div>
			</div>
		<logic:equal name="hydrationForm" property="has_aggregate" value="true">
			<div id="ch_precipitation" class="to-reload">
		</logic:equal>
		<logic:equal name="hydrationForm" property="has_aggregate" value="false">
			<div id="ch_precipitation" class="hidden to-reload">
		</logic:equal>
				Precipitation of CH on aggregate surfaces:
				<div class="radio-buttons-group">
					<html:radio property="ch_precipitation" value="prohibited" /> prohibited<br/>
					<html:radio property="ch_precipitation" value="allowed" /> allowed<br/>
				</div>
			</div>
	</div>
</div>
<div id="surface-deactivation" class="collapsable-element">
	<div id="surface-deactivation-title" class="collapsable-title collapsed"><a onclick="collapseExpand('surface-deactivation');">Surface deactivation</a></div>
	<div id="surface-deactivation-content" class="collapsable-content collapsed box-content">
		<table>
			<tr>
				<th>
					Phase
				</th>
				<th>
					Fraction of<BR/>Surface to<BR/>Deactivate
				</th>
				<th>
					Time to<BR/>Deactivate (h)
				</th>
				<th>
					Time to Begin<BR/>Reactivation (h)
				</th>
				<th>
					Time at Full<BR/>Reactivation (h)
				</th>
			</tr>
			<logic:iterate name="hydrationForm" property="surface_deactivations" id="surface_deactivation" indexId="ind">
				<tr>
					<td>
						<div id="phase_id_<%=ind%>" class="phase_id to-reload">
							<html:hidden name="surface_deactivation" property="phase_id" indexed="true" />
						</div>
						<div id="phase_name_<%=ind%>" class="phase_name to-reload">
							<bean:write name="surface_deactivation" property="phase_html_code" filter="false" />
						</div>
					</td>
					<td>
						<div id="surface_fraction_to_deactivate_<%=ind%>" class="surface_fraction_to_deactivate to-reload">
							<html:text name="surface_deactivation" property="surface_fraction_to_deactivate" indexed="true" size="6" onchange="checkFieldValue(this,'The surface fraction');" />
						</div>
					</td>
					<td>
						<div id="deactivation_time_<%=ind%>" class="deactivation_time to-reload">
							<html:text name="surface_deactivation" property="deactivation_time" indexed="true" size="6" onchange="onChangeDeactivationTime(this);" />
						</div>
					</td>
					<td>
						<div id="reactivation_begin_time_<%=ind%>" class="reactivation_begin_time to-reload">
							<html:text name="surface_deactivation" property="reactivation_begin_time" indexed="true" size="6" onchange="onChangeReactivationBeginTime(this);" />
						</div>
					</td>
					<td>
						<div id="full_reactivation_time_<%=ind%>" class="full_reactivation_time to-reload">
							<html:text name="surface_deactivation" property="full_reactivation_time" indexed="true" size="6" onchange="onChangeFullReactivationTime(this);" />
						</div>
					</td>
				</tr>
			</logic:iterate>
		</table>
	</div>
</div>
<div id="reactions-seeding" class="collapsable-element">
	<div id="reactions-seeding-title" class="collapsable-title collapsed"><a onclick="collapseExpand('reactions-seeding');">CSH Nucleation Seeding</a></div>
	<div id="reactions-seeding-content" class="collapsable-content collapsed box-content">
		<div id="csh_seeds" class="to-reload">
			Number of CSH seeds:
			<html:text property="csh_seeds" size="5" onchange="onChangeCsh_seeds(this);"/> x 10<sup>12</sup> seeds/mL<span id="csh_seeds" class="help-icon"></span>
                </div>
	</div>
</div>