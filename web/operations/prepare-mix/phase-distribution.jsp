<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>

<table>
	<tr>
		<th>
			Phase
		</th>
		<th>
			Volume fraction
		</th>
		<th>
			Surface area fraction
		</th>
		<th/>
	</tr>
	<tr>
		<td>
			C<sub>3</sub>S
		</td>
		<td>
			<span id="c3s_vf"><html:text size="6" property="c3s_vf" onchange="onChangePhaseVolumeFraction(this)" /></span>
		</td>
		<td>
			<span id="c3s_saf"><html:text size="6" property="c3s_saf" onchange="onChangePhaseSurfaceAreaFraction(this)" /></span>
		</td>
		<td/>
	</tr>
	<tr>
		<td>
			C<sub>2</sub>S
		</td>
		<td>
			<span id="c2s_vf"><html:text size="6" property="c2s_vf" onchange="onChangePhaseVolumeFraction(this)" /></span>
		</td>
		<td>
			<span id="c2s_saf"><html:text size="6" property="c2s_saf" onchange="onChangePhaseSurfaceAreaFraction(this)" /></span>
		</td>
		<td/>
	</tr>
	<tr>
		<td>
			C<sub>3</sub>A
		</td>
		<td>
			<span id="c3a_vf"><html:text size="6" property="c3a_vf" onchange="onChangePhaseVolumeFraction(this)" /></span>
		</td>
		<td>
			<span id="c3a_saf"><html:text size="6" property="c3a_saf" onchange="onChangePhaseSurfaceAreaFraction(this)" /></span>
		</td>
		<td>
			<span id="fraction_orthorombic_c3a">Fraction that is orthorhombic: <html:text size="4" property="fraction_orthorombic_c3a" /></span>
		</td>
	</tr>
	<tr>
		<td>
			C<sub>4</sub>AF
		</td>
		<td>
			<span id="c4af_vf"><html:text size="6" property="c4af_vf" onchange="onChangePhaseVolumeFraction(this)" /></span>
		</td>
		<td>
			<span id="c4af_saf"><html:text size="6" property="c4af_saf" onchange="onChangePhaseSurfaceAreaFraction(this)" /></span>
		</td>
		<td/>
	</tr>
	<tr>
		<td>
			K<sub>2</sub>SO<sub>4</sub>
		</td>
		<td>
			<logic:equal name="mixingForm" property="k2so4_corr" value="true" >
				<span id="k2so4_vf"><html:text size="6" property="k2so4_vf" onchange="onChangePhaseVolumeFraction(this)" /></span>
			</logic:equal>
			<logic:equal name="mixingForm" property="k2so4_corr" value="false" >
				<span id="k2so4_vf"><html:text size="6" property="k2so4_vf" readonly="readonly" styleClass="read-only-input" /></span>
			</logic:equal>
		</td>
		<td>
			<logic:equal name="mixingForm" property="k2so4_corr" value="true" >
				<span id="k2so4_saf"><html:text size="6" property="k2so4_saf" onchange="onChangePhaseSurfaceAreaFraction(this)" /></span>
			</logic:equal>
			<logic:equal name="mixingForm" property="k2so4_corr" value="false" >
				<span id="k2so4_saf"><html:text size="6" property="k2so4_saf" readonly="readonly" styleClass="read-only-input" /></span>
			</logic:equal>
		</td>
		<td/>
	</tr>
	<tr>
		<td>
			Na<sub>2</sub>SO<sub>4</sub>
		</td>
		<td>
			<logic:equal name="mixingForm" property="na2so4_corr" value="true" >
				<span id="na2so4_vf"><html:text size="6" property="na2so4_vf" onchange="onChangePhaseVolumeFraction(this)" /></span>
			</logic:equal>
			<logic:equal name="mixingForm" property="na2so4_corr" value="false" >
				<span id="na2so4_vf"><html:text size="6" property="na2so4_vf" readonly="readonly" styleClass="read-only-input" /></span>
			</logic:equal>
		</td>
		<td>
			<logic:equal name="mixingForm" property="na2so4_corr" value="true" >
				<span id="na2so4_saf"><html:text size="6" property="na2so4_saf" onchange="onChangePhaseSurfaceAreaFraction(this)" /></span>
			</logic:equal>
			<logic:equal name="mixingForm" property="na2so4_corr" value="false" >
				<span id="na2so4_saf"><html:text size="6" property="na2so4_saf" readonly="readonly" styleClass="read-only-input" /></span>
			</logic:equal>
		</td>
		<td/>
	</tr>
	<tr>
		<td colspan="3">
			<hr/>
		</td>
	</tr>
	<tr>
		<td>
			Sum:
		</td>
		<td>
			<span id="sum_vf"><html:text size="6" property="sum_vf" readonly="readonly" styleClass="read-only-input" /></span>
		</td>
		<td>
			<span id="sum_saf"><html:text size="6" property="sum_saf" readonly="readonly" styleClass="read-only-input" /></span>
		</td>
	</tr>
</table>