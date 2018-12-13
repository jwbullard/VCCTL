var WATER_DENSITY = 0.997;
var SILICA_FUME_SPECIFIC_GRAVITY = 2.2;
var CACO3_SPECIFIC_GRAVITY = 2.71;
var FREE_LIME_SPECIFIC_GRAVITY = 3.31;
var DIHYDRATE_SPECIFIC_GRAVITY = 2.32;
var HEMIHYDRATE_SPECIFIC_GRAVITY = 2.74;
var ANHYDRITE_SPECIFIC_GRAVITY = 2.61;
var C3S_SPECIFIC_GRAVITY = 3.21;
var C2S_SPECIFIC_GRAVITY = 3.28;
var C3A_SPECIFIC_GRAVITY = 3.038;
var ORTHORHOMBIC_C3A_SPECIFIC_GRAVITY = 3.052;
var C4AF_SPECIFIC_GRAVITY = 3.73;
var K2SO4_SPECIFIC_GRAVITY = 2.662;
var NA2SO4_SPECIFIC_GRAVITY = 2.68;
var SIZE_SAFETY_COEFFICIENT = 1.0/3.0;
var RESOLUTION_SAFETY_COEFFICIENT = 2.5;
var SYSTEM_SIZE_LIMIT = Math.pow(2,26);
var MAX_PIXELS_WARNING = 8000000;
var MAX_PIXELS_ERROR = 64000000;

/**
* Phase distribution functions
*/

function onChangePhaseVolumeFraction(theField) {
    /**
	* Sum volume fractions
	*/
    theForm = theField.form;
    var sum = 0.0;
    var value = checkAndGetValueOfField(theField);

    /**
	* If new value = 0, set coressponding surface area fraction to 0
	*/
    if (value == 0) {
        var surfaceAreaFractionFieldName = theField.name.replace('_vf','_saf');
        theForm[surfaceAreaFractionFieldName].value = '0.0';
        sumPhaseSurfaceAreaFractions(theForm);
    }

    sumPhaseVolumeFractions(theForm);
    theField.value = value.toNiceFixed(4);

    /**
	* Update calcium sulfates volume fractions because the cement specific gravity changed
	*/
    onChangeSulfateMassFraction(theField);
}

function onChangePhaseSurfaceAreaFraction(theField) {
    /**
	* Sum surface area fractions
	*/
    theForm = theField.form;
    var sum = 0.0;
    var value = checkAndGetValueOfField(theField);

    /**
	* If new value = 0, set coressponding volume fraction to 0
	*/
    if (value == 0) {
        var volumeFractionFieldName = theField.name.replace('_saf','_vf');
        theForm[volumeFractionFieldName].value = '0.0';
        sumPhaseVolumeFractions(theForm);
        /**
		* Update calcium sulfates volume fractions because the cement specific gravity changed
		*/
        onChangeSulfateMassFraction(theForm[volumeFractionFieldName]);
    }

    sumPhaseSurfaceAreaFractions(theForm);
    theField.value = value.toNiceFixed(4);
}

function sumPhaseVolumeFractions(theForm) {
    var sum = 0.0;

    sum += checkAndGetValueOfField(theForm.c3s_vf, "The volume fraction of C3S");
    sum += checkAndGetValueOfField(theForm.c2s_vf, "The volume fraction of C2S");
    sum += checkAndGetValueOfField(theForm.c3a_vf, "The volume fraction of C3A");
    sum += checkAndGetValueOfField(theForm.c4af_vf, "The volume fraction of C4AF");
    sum += checkAndGetValueOfField(theForm.k2so4_vf, "The volume fraction of K2SO4");
    sum += checkAndGetValueOfField(theForm.na2so4_vf, "The volume fraction of Na2SO4");

    if (sum == 0) {
        alert("You must have at least one phase in the clinker");
        theForm.c3s_vf.value = 1.0;
        theForm.c3s_saf.value = 1.0;
        onChangePhaseVolumeFraction(theForm.c3s_vf);
        onChangePhaseSurfaceAreaFraction(theForm.c3s_saf);
        return;
    }
    theForm.sum_vf.value = sum.toNiceFixed(4);
}

function sumPhaseSurfaceAreaFractions(theForm) {
    var sum = 0.0;

    sum += checkAndGetValueOfField(theForm.c3s_saf, "The surface area fraction of C3S");
    sum += checkAndGetValueOfField(theForm.c2s_saf, "The surface area fraction of C2S");
    sum += checkAndGetValueOfField(theForm.c3a_saf, "The surface area fraction of C3A");
    sum += checkAndGetValueOfField(theForm.c4af_saf, "The surface area fraction of C4AF");
    sum += checkAndGetValueOfField(theForm.k2so4_saf, "The surface area fraction of K2SO4");
    sum += checkAndGetValueOfField(theForm.na2so4_saf, "The surface area fraction of Na2SO4");

    if (sum == 0) {
        alert("You must have at least one phase in the clinker");
        theForm.c3s_vf.value = 1.0;
        theForm.c3s_saf.value = 1.0;
        onChangePhaseVolumeFraction(theForm.c3s_vf);
        onChangePhaseSurfaceAreaFraction(theForm.c3s_saf);
        return;
    }

    theForm.sum_saf.value = sum.toNiceFixed(4);
}


/**
* Calcium sulfates functions
*/

function onChangeSulfateMassFraction(theField) {
    theForm = theField.form;
    var massFrac;
    var volFrac;
    var sum = 0;

    sum += checkAndGetValueOfField(theForm.dihydrate_massfrac, "The mass fraction of dihydrate");
    sum += checkAndGetValueOfField(theForm.hemihydrate_massfrac, "The mass fraction of hemihydrate");
    sum += checkAndGetValueOfField(theForm.hemihydrate_massfrac, "The mass fraction of hemihydrate");

    if (sum >= 1) {
        alert("Total of calcium sulfates volume fractions must be in the range [0.0,1.0]");
        theField.value="0.0";
        theField.focus();
    }

    var cementSpecificGravity = calculateCementSpecificGravityWithCalciumSulfatesMassFractions(theForm);

    /* Dihydrate */
    massFrac = parseFloat(theForm.dihydrate_massfrac.value);
    volFrac = massFrac * cementSpecificGravity / DIHYDRATE_SPECIFIC_GRAVITY;
    theForm.dihydrate_volfrac.value = volFrac.toNiceFixed(4);

    /* Hemihydrate */
    massFrac = parseFloat(theForm.hemihydrate_massfrac.value);
    volFrac = massFrac * cementSpecificGravity / HEMIHYDRATE_SPECIFIC_GRAVITY;
    theForm.hemihydrate_volfrac.value = volFrac.toNiceFixed(4);

    /* Anhydrite */
    massFrac = parseFloat(theForm.anhydrite_massfrac.value);
    volFrac = massFrac * cementSpecificGravity / ANHYDRITE_SPECIFIC_GRAVITY;
    theForm.anhydrite_volfrac.value = volFrac.toNiceFixed(4);

    updateMixVolumeFractions(theForm);
}

function onChangeSulfateVolumeFraction(theField) {
    theForm = theField.form;
    var massFrac;
    var volFrac;
    var sum = 0;

    sum += checkAndGetValueOfField(theForm.dihydrate_volfrac, "The volume fraction of dihydrate");
    sum += checkAndGetValueOfField(theForm.hemihydrate_volfrac, "The volume fraction of hemihydrate");
    sum += checkAndGetValueOfField(theForm.anhydrite_volfrac, "The volume fraction of anhydrite");

    if (sum >= 1) {
        alert("Total of calcium sulfates mass fractions must be in the range [0.0,1.0[");
        theField.value="0.0";
        theField.focus();
    }

    var cementSpecificGravity = calculateCementSpecificGravityWithCalciumSulfatesVolumeFractions(theForm);

    /* Dihydrate */
    volFrac = parseFloat(theForm.dihydrate_volfrac.value);
    massFrac = (DIHYDRATE_SPECIFIC_GRAVITY*volFrac)/cementSpecificGravity;
    theForm.dihydrate_massfrac.value=massFrac.toNiceFixed(4);
    /* Hemihydrate */
    volFrac = parseFloat(theForm.hemihydrate_volfrac.value);
    massFrac = (HEMIHYDRATE_SPECIFIC_GRAVITY*volFrac)/cementSpecificGravity;
    theForm.hemihydrate_massfrac.value=massFrac.toNiceFixed(4);
    /* Anhydrite */
    volFrac = parseFloat(theForm.anhydrite_volfrac.value);
    massFrac = (ANHYDRITE_SPECIFIC_GRAVITY*volFrac)/cementSpecificGravity;
    theForm.anhydrite_massfrac.value=massFrac.toNiceFixed(4);

    updateMixVolumeFractions(theForm);
}

function calculateCementSpecificGravityWithCalciumSulfatesMassFractions(theForm) {
    var clinkerSpecificGravity = 0;
    var totalVolume = 0;
    var clinkerMassFraction; // mass fraction of clinker in CEMENT (not just clinker. cement = clinker + calcium sulfates)
    var volume;

    /**
	* Calculate mass fraction of clinker in cement
	**/
    var dihydrateMassFraction = parseFloat(theForm.dihydrate_massfrac.value);
    var hemihydrateMassFraction = parseFloat(theForm.hemihydrate_massfrac.value);
    var anhydriteMassFraction = parseFloat(theForm.anhydrite_massfrac.value);
    clinkerMassFraction = 1 - dihydrateMassFraction - hemihydrateMassFraction - anhydriteMassFraction;

    /**
	* Normalize volume fractions in CLINKER and calculate the specific gravity of the clinker
	**/
    var c3sVolumeFraction = parseFloat(theForm.c3s_vf.value);
    totalVolume += c3sVolumeFraction;

    var c2sVolumeFraction = parseFloat(theForm.c2s_vf.value);
    totalVolume += c2sVolumeFraction;

    var c3aVolumeFraction = parseFloat(theForm.c3a_vf.value);
    totalVolume += c3aVolumeFraction;

    var c4afVolumeFraction = parseFloat(theForm.c4af_vf.value);
    totalVolume += c4afVolumeFraction;

    var k2so4VolumeFraction = parseFloat(theForm.k2so4_vf.value);
    totalVolume += k2so4VolumeFraction;

    var na2so4VolumeFraction = parseFloat(theForm.na2so4_vf.value);
    totalVolume += na2so4VolumeFraction;

    c3sVolumeFraction /= totalVolume;
    clinkerSpecificGravity += c3sVolumeFraction * C3S_SPECIFIC_GRAVITY;

    c2sVolumeFraction /= totalVolume;
    clinkerSpecificGravity += c2sVolumeFraction * C2S_SPECIFIC_GRAVITY;

    c3aVolumeFraction /= totalVolume;
    clinkerSpecificGravity += c3aVolumeFraction * C3A_SPECIFIC_GRAVITY;

    c4afVolumeFraction /= totalVolume;
    clinkerSpecificGravity += c4afVolumeFraction * C4AF_SPECIFIC_GRAVITY;

    k2so4VolumeFraction /= totalVolume;
    clinkerSpecificGravity += k2so4VolumeFraction * K2SO4_SPECIFIC_GRAVITY;

    na2so4VolumeFraction /= totalVolume;
    clinkerSpecificGravity += na2so4VolumeFraction * NA2SO4_SPECIFIC_GRAVITY;

    /**
	* Calculate total volume in 1g of CEMENT
	**/
    totalVolume = 0;
    totalVolume += c3sVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
    totalVolume += c2sVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
    totalVolume += c3aVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
    totalVolume += c4afVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
    totalVolume += k2so4VolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
    totalVolume += na2so4VolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
    totalVolume += dihydrateMassFraction / DIHYDRATE_SPECIFIC_GRAVITY;
    totalVolume += hemihydrateMassFraction / HEMIHYDRATE_SPECIFIC_GRAVITY;
    totalVolume += anhydriteMassFraction / ANHYDRITE_SPECIFIC_GRAVITY;

    return 1 / totalVolume; // mass = 1
}

function calculateCementSpecificGravityWithCalciumSulfatesVolumeFractions(theForm) {
    var specificGravity = 0;
    var totalVolume = 0;
    var clinkerVolumeFraction; // mass fraction of clinker in CEMENT (not just clinker. cement = clinker + calcium sulfates)

    /**
	* Calculate volume fraction of clinker in cement
	**/
    var dihydrateVolumeFraction = parseFloat(theForm.dihydrate_volfrac.value);
    var hemihydrateVolumeFraction = parseFloat(theForm.hemihydrate_volfrac.value);
    var anhydriteVolumeFraction = parseFloat(theForm.anhydrite_volfrac.value);
    clinkerVolumeFraction = 1 - dihydrateVolumeFraction - hemihydrateVolumeFraction - anhydriteVolumeFraction;

    /**
	* Normalize volume fractions in CEMENT (normalize volume fractions in CLINKER and multiply by the volume fraction of clinker)
	**/
    var c3sVolumeFraction = parseFloat(theForm.c3s_vf.value);
    totalVolume += c3sVolumeFraction;

    var c2sVolumeFraction = parseFloat(theForm.c2s_vf.value);
    totalVolume += c2sVolumeFraction;

    var c3aVolumeFraction = parseFloat(theForm.c3a_vf.value);
    totalVolume += c3aVolumeFraction;

    var c4afVolumeFraction = parseFloat(theForm.c4af_vf.value);
    totalVolume += c4afVolumeFraction;

    var k2so4VolumeFraction = parseFloat(theForm.k2so4_vf.value);
    totalVolume += k2so4VolumeFraction;

    var na2so4VolumeFraction = parseFloat(theForm.na2so4_vf.value);
    totalVolume += na2so4VolumeFraction;

    c3sVolumeFraction *= clinkerVolumeFraction / totalVolume;
    specificGravity += c3sVolumeFraction * C3S_SPECIFIC_GRAVITY;

    c2sVolumeFraction *= clinkerVolumeFraction / totalVolume;
    specificGravity += c2sVolumeFraction * C2S_SPECIFIC_GRAVITY;

    c3aVolumeFraction *= clinkerVolumeFraction / totalVolume;
    specificGravity += c3aVolumeFraction * C3A_SPECIFIC_GRAVITY;

    c4afVolumeFraction *= clinkerVolumeFraction / totalVolume;
    specificGravity += c4afVolumeFraction * C4AF_SPECIFIC_GRAVITY;

    k2so4VolumeFraction *= clinkerVolumeFraction / totalVolume;
    specificGravity += k2so4VolumeFraction * K2SO4_SPECIFIC_GRAVITY;

    na2so4VolumeFraction *= clinkerVolumeFraction / totalVolume;
    specificGravity += na2so4VolumeFraction * NA2SO4_SPECIFIC_GRAVITY;

    specificGravity += dihydrateVolumeFraction * DIHYDRATE_SPECIFIC_GRAVITY;
    specificGravity += hemihydrateVolumeFraction * HEMIHYDRATE_SPECIFIC_GRAVITY;
    specificGravity += anhydriteVolumeFraction * ANHYDRITE_SPECIFIC_GRAVITY;

    return specificGravity;
}



/**
* SCM functions
*/

var savedMassFractions = new Array();
var savedVolumeFractions = new Array();

function addOrRemoveCementitiousMaterial(theForm,materialName) {
    var massFracField = materialName + "_massfrac";
    var volFracField = materialName + "_volfrac";
    var checkBoxName = "add_" + materialName + "_checkbox";
    var add_material = "add_" + materialName;
    var cementMassFrac = parseFloat(theForm["cement_massfrac"].value);
    var cementVolFrac = parseFloat(theForm["cement_volfrac"].value);
    var frac;

    theForm[add_material].value = theForm[checkBoxName].checked;

    if (theForm[checkBoxName].checked) {
        enableOrDisableCementitiousMaterialLine(true,theForm,materialName);
        frac = savedMassFractions[materialName];
        if (frac > 0) {
            theForm[massFracField].value = frac.toNiceFixed(4);
            theForm["cement_massfrac"].value = (cementMassFrac - frac).toNiceFixed(4);
        }
        frac = savedVolumeFractions[materialName];
        if (frac > 0) {
            theForm[volFracField].value = frac.toNiceFixed(4);
            theForm["cement_volfrac"].value = (cementVolFrac - frac).toNiceFixed(4);
        }
    }
    else {
        enableOrDisableCementitiousMaterialLine(false,theForm,materialName);
        frac = parseFloat(theForm[massFracField].value);
        savedMassFractions[materialName] = frac;
        theForm["cement_massfrac"].value = (cementMassFrac + frac).toNiceFixed(4);
        theForm[massFracField].value = (0).toNiceFixed(4);
        frac = parseFloat(theForm[volFracField].value);
        savedVolumeFractions[materialName] = frac;
        theForm["cement_volfrac"].value = (cementVolFrac + frac).toNiceFixed(4);
        theForm[volFracField].value = (0).toNiceFixed(4);
    }
}

function enableOrDisableCementitiousMaterialLine(enable,theForm,materialName) {
    var massFracField = materialName + "_massfrac";
    var volFracField = materialName + "_volfrac";
    var checkBoxName = "add_" + materialName + "_checkbox";
    var materialPopupMenu = materialName + "_psd";
    theForm[checkBoxName].checked = enable;
    theForm[massFracField].disabled = (!enable);
    theForm[volFracField].disabled = (!enable);
    theForm[materialPopupMenu].disabled = (!enable);
}

function enableOrDisableCementitiousMaterialLines() {
    theForm = document.forms[0];
    var materialNames = new Array();
    materialNames[0] = "fly_ash";
    materialNames[1] = "slag";
    materialNames[2] = "inert_filler";
    materialNames[3] = "silica_fume";
    materialNames[4] = "caco3";
    materialNames[5] = "free_lime";
    for (var i=0; i<materialNames.length;i++) {
        var checkBoxName = "add_" + materialNames[i];
        var massFracField = materialNames[i] + "_massfrac";
        enable = (theForm[checkBoxName].checked) || (parseFloat(theForm[massFracField].value) > 0.0);
        enableOrDisableCementitiousMaterialLine(enable,theForm,materialNames[i]);
    }
}

function onChangeCementitiousMaterialMassFraction(theElement,materialName) {
    /* Sum up all of the solid mass fractions */
    var sum = 0.0;
    var sum_vol = 0.0;
    var theForm = theElement.form;

    /* Silica fume: SG=SILICA_FUME_SPECIFIC_GRAVITY */
    var mfi = checkAndGetValueOfField(theForm.silica_fume_massfrac, "The mass fraction of silica fume");
    sum = sum + mfi;
    var vol_silica_fume = mfi/SILICA_FUME_SPECIFIC_GRAVITY;
    sum_vol = sum_vol + vol_silica_fume;
    theForm.silica_fume_massfrac.value=mfi.toNiceFixed(4);

    /* Fly ash */
    mfi = checkAndGetValueOfField(theForm.fly_ash_massfrac, "The mass fraction of fly ash");
    sum = sum + mfi;
    var fly_ash_sg = parseFloat(theForm.fly_ash_sg.value);
    var vol_fly_ash = mfi/fly_ash_sg;
    sum_vol = sum_vol + vol_fly_ash;
    theForm.fly_ash_massfrac.value=mfi.toNiceFixed(4);

    /* Slag */
    mfi = checkAndGetValueOfField(theForm.slag_massfrac, "The mass fraction of slag");
    sum = sum + mfi;
    var slag_sg = parseFloat(theForm.slag_sg.value);
    var vol_slag = mfi/slag_sg;
    sum_vol = sum_vol + vol_slag;
    theForm.slag_massfrac.value=mfi.toNiceFixed(4);

    /* CaCO3: SG=CACO3_SPECIFIC_GRAVITY */
    mfi = checkAndGetValueOfField(theForm.caco3_massfrac, "The mass fraction of CaCO3");
    sum = sum + mfi;
    var vol_caco3 = mfi/CACO3_SPECIFIC_GRAVITY;
    sum_vol = sum_vol + vol_caco3;
    theForm.caco3_massfrac.value=mfi.toNiceFixed(4);

    /* Free Lime: SG=FREE_LIME_SPECIFIC_GRAVITY */
    mfi = checkAndGetValueOfField(theForm.free_lime_massfrac, "The mass fraction of free lime");
    sum = sum + mfi;
    var vol_free_lime = mfi/FREE_LIME_SPECIFIC_GRAVITY;
    sum_vol = sum_vol + vol_free_lime;
    theForm.free_lime_massfrac.value=mfi.toNiceFixed(4);

    /* Inert Filler */
    mfi = checkAndGetValueOfField(theForm.inert_filler_massfrac, "The mass fraction of inert filler");
    sum = sum + mfi;
    var inert_filler_sg = parseFloat(theForm.inert_filler_sg.value);
    var vol_inert_filler = mfi/inert_filler_sg;
    sum_vol = sum_vol + vol_inert_filler;
    theForm.inert_filler_massfrac.value=mfi.toNiceFixed(4);

    if (sum > 1) {
        alert("Total of SCM mass fractions must be in the range [0.0,1.0]");
        sum = sum - theElement.value;
        theElement.value="0.0";
        theElement.focus();
        onChangeCementitiousMaterialMassFraction(theElement,materialName);
        return false;
    }

    /* Calculate the cement mass fraction.*/
    var cmf = 1 - sum;
    theForm.cement_massfrac.value=cmf.toNiceFixed(4);
    var vol_cement = cmf/calculateCementSpecificGravityWithCalciumSulfatesMassFractions(theForm);
    sum_vol = sum_vol + vol_cement;

    /* Calculate volume fractions from mass fraction */
    /*
	var vfw = vol_water/sum_vol;
	theForm.water_volfrac.value=vfw.toNiceFixed(4);
	*/
    var svf = vol_cement/sum_vol;
    theForm.cement_volfrac.value=svf.toNiceFixed(4);
    svf = vol_silica_fume/sum_vol;
    theForm.silica_fume_volfrac.value=svf.toNiceFixed(4);
    svf = vol_fly_ash/sum_vol;
    theForm.fly_ash_volfrac.value=svf.toNiceFixed(4);
    svf = vol_slag/sum_vol;
    theForm.slag_volfrac.value=svf.toNiceFixed(4);
    svf = vol_caco3/sum_vol;
    theForm.caco3_volfrac.value=svf.toNiceFixed(4);
    svf = vol_free_lime/sum_vol;
    theForm.free_lime_volfrac.value=svf.toNiceFixed(4);
    svf = vol_inert_filler/sum_vol;
    theForm.inert_filler_volfrac.value=svf.toNiceFixed(4);

    /* Disable line if the volume fraction is not > 0 */
    var massFracField = materialName + "_massfrac";
    var massFrac = theForm[massFracField].value;
    if (massFrac <= 0.0) {
        enableOrDisableCementitiousMaterialLine(false,theForm,materialName);
    }

    updateMixVolumeFractions(theForm);

    return true;
}

function onChangeCementitiousMaterialVolumeFraction(theElement,materialName) {
    /* Sum up all of the solid volume fractions */
    var sum = 0.0;
    var sum_mass = 0.0;
    theForm = theElement.form;

    /* Silica fume: SG=SILICA_FUME_SPECIFIC_GRAVITY */
    var vfi = checkAndGetValueOfField(theForm.silica_fume_volfrac, "The volume fraction of silica fume");
    sum = sum + vfi;
    var mass_silica_fume = vfi*SILICA_FUME_SPECIFIC_GRAVITY;
    sum_mass = sum_mass + mass_silica_fume;
    theForm.silica_fume_volfrac.value=vfi.toNiceFixed(4);

    /* Fly ash */
    vfi = checkAndGetValueOfField(theForm.fly_ash_volfrac, "The volume fraction of fly ash");
    sum = sum + vfi;
    var fly_ash_sg = parseFloat(theForm.fly_ash_sg.value);
    var mass_fly_ash = vfi*fly_ash_sg;
    sum_mass = sum_mass + mass_fly_ash;
    theForm.fly_ash_volfrac.value=vfi.toNiceFixed(4);

    /* Slag */
    vfi = checkAndGetValueOfField(theForm.slag_volfrac, "The volume fraction of slag");
    sum = sum + vfi;
    var slag_sg = parseFloat(theForm.slag_sg.value);
    var mass_slag = vfi*slag_sg;
    sum_mass = sum_mass + mass_slag;
    theForm.slag_volfrac.value=vfi.toNiceFixed(4);

    /* CaCO3: SG=CACO3_SPECIFIC_GRAVITY */
    vfi = checkAndGetValueOfField(theForm.caco3_volfrac, "The volume fraction of CaCO3");
    sum = sum + vfi;
    var mass_caco3 = vfi*CACO3_SPECIFIC_GRAVITY;
    sum_mass = sum_mass + mass_caco3;
    theForm.caco3_volfrac.value=vfi.toNiceFixed(4);

    /* Free Lime: SG=FREE_LIME_SPECIFIC_GRAVITY */
    vfi = checkAndGetValueOfField(theForm.free_lime_volfrac, "The volume fraction of free lime");
    sum = sum + vfi;
    var mass_free_lime = vfi*FREE_LIME_SPECIFIC_GRAVITY;
    sum_mass = sum_mass + mass_free_lime;
    theForm.free_lime_volfrac.value=vfi.toNiceFixed(4);

    /* Inert Filler */
    vfi = checkAndGetValueOfField(theForm.inert_filler_volfrac, "The volume fraction of inert filler");
    sum = sum + vfi;
    var inert_filler_sg = parseFloat(theForm.inert_filler_sg.value);
    // var mass_inert_filler = vfi*3.0;
    var mass_inert_filler = vfi*inert_filler_sg;
    sum_mass = sum_mass + mass_inert_filler;
    theForm.inert_filler_volfrac.value=vfi.toNiceFixed(4);

    if (sum > 1) {
        alert("Total of SCM volume fractions must be in the range [0.0,1.0]");
        sum = sum - theElement.value;
        theElement.value="0.0";
        theElement.focus();
        onChangeCementitiousMaterialVolumeFraction(theElement,materialName);
        return false;
    }

    /* Cement: */
    var cvf = 1 - sum;
    theForm.cement_volfrac.value=cvf.toNiceFixed(4);
    sum = sum + cvf;
    var mass_cement = cvf*calculateCementSpecificGravityWithCalciumSulfatesMassFractions(theForm);
    sum_mass = sum_mass + mass_cement;


    /* Calculate mass fractions from volume fraction */
    /*
	var mfw = mass_water/sum_mass;
	theForm.water_massfrac.value=mfw.toNiceFixed(4);
	*/
    var smf = mass_cement/sum_mass;
    theForm.cement_massfrac.value=smf.toNiceFixed(4);
    smf = mass_silica_fume/sum_mass;
    theForm.silica_fume_massfrac.value=smf.toNiceFixed(4);
    smf = mass_fly_ash/sum_mass;
    theForm.fly_ash_massfrac.value=smf.toNiceFixed(4);
    smf = mass_slag/sum_mass;
    theForm.slag_massfrac.value=smf.toNiceFixed(4);
    smf = mass_caco3/sum_mass;
    theForm.caco3_massfrac.value=smf.toNiceFixed(4);
    smf = mass_free_lime/sum_mass;
    theForm.free_lime_massfrac.value=smf.toNiceFixed(4);
    smf = mass_inert_filler/sum_mass;
    theForm.inert_filler_massfrac.value=smf.toNiceFixed(4);

    /* Disable line if the voulume fraction is not > 0 */
    var volFracField = materialName + "_volfrac";
    var volFrac = theForm[volFracField].value;
    if (volFrac <= 0.0) {
        enableOrDisableCementitiousMaterialLine(false,theForm,materialName);
    }

    updateMixVolumeFractions(theForm);

    return true;
}



/**
* Mixing proportions functions
*/

function updateBinderSpecificGravity(theForm) {
    // Verify that it's correct
    var cementMassFrac = parseFloat(theForm.cement_massfrac.value);
    var cementVolumeFrac = parseFloat(theForm.cement_volfrac.value);
    theForm.binder_sg.value = (cementVolumeFrac/cementMassFrac)*calculateCementSpecificGravityWithCalciumSulfatesMassFractions(theForm);
}

function onChangeBinderMassFraction(binderMassFracField) {
    theForm = binderMassFracField.form;
    onChangeBinderFractionOfType(binderMassFracField,'mass');
    updateMixVolumeFractions(theForm);
}

function onChangeBinderVolumeFraction(binderVolumeFracField) {
    theForm = binderVolumeFracField.form;
    onChangeBinderFractionOfType(binderVolumeFracField,'vol');
    updateMixMassFractions(theForm);
}

function onChangeBinderFractionOfType(binderFracField,fractionType) {
    var theForm = binderFracField.form;
    var binderFrac = checkAndGetValueOfField(binderFracField,'The '+fractionType+' fraction');

    var coarseAggregate01Frac = parseFloat(theForm['coarse_aggregate01_'+fractionType+'frac'].value);
    var coarseAggregate02Frac = parseFloat(theForm['coarse_aggregate02_'+fractionType+'frac'].value);

    var fineAggregate01Frac = parseFloat(theForm['fine_aggregate01_'+fractionType+'frac'].value);
    var fineAggregate02Frac = parseFloat(theForm['fine_aggregate02_'+fractionType+'frac'].value);

    var waterFrac = parseFloat(theForm['water_'+fractionType+'frac'].value);

    var newWaterFrac = 1 - binderFrac - coarseAggregate01Frac - coarseAggregate02Frac - fineAggregate01Frac - fineAggregate02Frac;
    var sumOK = ((newWaterFrac >= 0) && (newWaterFrac <= 1));
    if (sumOK) {
        theForm['water_'+fractionType+'frac'].value = newWaterFrac.toNiceFixed(4);
    } else {
        alert('Total of '+fractionType+' fractions cannot exceed 1.0');
        binderFrac = 1 - waterFrac - coarseAggregate01Frac - coarseAggregate02Frac - fineAggregate01Frac - fineAggregate02Frac;
        binderFracField.value = binderFrac.toNiceFixed(4);
    }
}

function onChangeWaterMassFraction(waterMassFracField) {
    theForm = waterMassFracField.form;
    onChangeWaterFractionOfType(waterMassFracField,'mass');
    updateMixVolumeFractions(theForm);
}

function onChangeWaterVolumeFraction(waterVolumeFracField) {
    theForm = waterVolumeFracField.form;
    onChangeWaterFractionOfType(waterVolumeFracField,'vol');
    updateMixMassFractions(theForm);
}

function onChangeWaterFractionOfType(waterFracField,fractionType) {
    var theForm = waterFracField.form;
    var waterFrac = checkAndGetValueOfField(waterFracField,'The '+fractionType+' fraction');

    var coarseAggregate01Frac = parseFloat(theForm['coarse_aggregate01_'+fractionType+'frac'].value);
    var coarseAggregate02Frac = parseFloat(theForm['coarse_aggregate02_'+fractionType+'frac'].value);
    var fineAggregate01Frac = parseFloat(theForm['fine_aggregate01_'+fractionType+'frac'].value);
    var fineAggregate02Frac = parseFloat(theForm['fine_aggregate02_'+fractionType+'frac'].value);
    var binderFrac = parseFloat(theForm['binder_'+fractionType+'frac'].value);

    var newBinderFrac = 1 - waterFrac - coarseAggregate01Frac - coarseAggregate02Frac - fineAggregate01Frac - fineAggregate02Frac;
    var sumOK = ((newBinderFrac >= 0) && (newBinderFrac <= 1));
    if (sumOK) {
        theForm['binder_'+fractionType+'frac'].value = newBinderFrac.toNiceFixed(4);
    } else {
        alert('Total of '+fractionType+' fractions cannot exceed 1.0');
        waterFrac = 1 - binderFrac - coarseAggregate01Frac - coarseAggregate02Frac - fineAggregate01Frac - fineAggregate02Frac;
        waterFracField.value = waterFrac.toNiceFixed(4);
    }
}

function onChangeWaterBinderRatio(waterBinderRatioField) {
    var theForm = waterBinderRatioField.form;
    var waterBinderRatio = checkAndGetValueOfField(waterBinderRatioField,'The water/binder ratio');

    var totalAggregateMassFrac = parseFloat(theForm['coarse_aggregate01_massfrac'].value) + parseFloat(theForm['fine_aggregate01_massfrac'].value);
    totalAggregateMassFrac += parseFloat(theForm['coarse_aggregate02_massfrac'].value) + parseFloat(theForm['fine_aggregate02_massfrac'].value);
    var newBinderMassFrac = (1 / (waterBinderRatio + 1)) * (1 - totalAggregateMassFrac);
    theForm['binder_massfrac'].value = newBinderMassFrac.toNiceFixed(4);
    var newWaterMassFrac = (waterBinderRatio / (waterBinderRatio + 1)) * (1 - totalAggregateMassFrac);
    theForm['water_massfrac'].value = newWaterMassFrac.toNiceFixed(4);
    updateMixVolumeFractions(theForm);
}

/**
* When changing aggregate mass fraction, change fraction of binder and water in order to keep the same water/solid ratio
**/
function onChangeAggregateMassFraction(aggregateMassFracField) {
    theForm = aggregateMassFracField.form;
    onChangeAggregateFraction(aggregateMassFracField,'mass');
    updateMixVolumeFractions(theForm);
}

/**
* When changing aggregate volume fraction, change fraction of binder and water in order to keep the same water/solid ratio
**/
function onChangeAggregateVolumeFraction(aggregateVolumeFracField) {
    theForm = aggregateVolumeFracField.form;
    onChangeAggregateFraction(aggregateVolumeFracField,'vol');
    updateMixMassFractions(theForm);
}

/**
* When changing aggregate mass fraction, change fraction of binder and water in order to keep the same water/solid ratio
**/
function onChangeAggregateFraction(aggregateFracField,fractionType) {
    theForm = aggregateFracField.form;

    checkFieldValue(aggregateFracField,'The ' + fractionType + ' fraction');
    verifyFractionValueOfType(aggregateFracField,fractionType);

    var totalAggregateFrac = parseFloat(theForm['coarse_aggregate01_' + fractionType + 'frac'].value) + parseFloat(theForm['fine_aggregate01_' + fractionType + 'frac'].value);
    totalAggregateFrac += parseFloat(theForm['coarse_aggregate02_' + fractionType + 'frac'].value) + parseFloat(theForm['fine_aggregate02_' + fractionType + 'frac'].value);

    var waterBinderRatio = parseFloat(theForm['water_' + fractionType + 'frac'].value) / parseFloat(theForm['binder_' + fractionType + 'frac'].value);

    var newBinderFrac = (1 / (waterBinderRatio + 1)) * (1 - totalAggregateFrac);
    theForm['binder_' + fractionType + 'frac'].value = newBinderFrac.toNiceFixed(4);
    var newWaterFrac = (waterBinderRatio / (waterBinderRatio + 1)) * (1 - totalAggregateFrac);
    theForm['water_' + fractionType + 'frac'].value = newWaterFrac.toNiceFixed(4);

    hideOrDisplayAirVolumeFraction(theForm);
}

function verifyFractionValueOfType(aggregateFracField,fractionType) {
    var theForm = aggregateFracField.form;
    var aggregateFrac = parseFloat(aggregateFracField.value);
    var aggregateName = aggregateFracField.name.substring(0,aggregateFracField.name.indexOf('_'+fractionType+'frac'));

    /**
     * Disable the line if the fraction = 0 for coarse or fine aggregate.
     **/
    if (aggregateFrac == 0) {
        switch (aggregateName)
        {
            case 'coarse_aggregate01':
                enableOrDisableAggregateLine(false,theForm,'coarse','01');
                savedMassFractions['coarse01'] = 0.0;
                savedVolumeFractions['coarse01'] = 0.0;
                break;

            case 'coarse_aggregate02':
                enableOrDisableAggregateLine(false,theForm,'coarse','02');
                savedMassFractions['coarse02'] = 0.0;
                savedVolumeFractions['coarse02'] = 0.0;
                break;

            case 'fine_aggregate01':
                enableOrDisableAggregateLine(false,theForm,'fine','01');
                savedMassFractions['fine01'] = 0.0;
                savedVolumeFractions['fine01'] = 0.0;
                break;

            case 'fine_aggregate02':
                enableOrDisableAggregateLine(false,theForm,'fine','02');
                savedMassFractions['fine02'] = 0.0;
                savedVolumeFractions['fine02'] = 0.0;
                break;
        }
    }
}

function saveCoarseGrading(theForm,num) {
    saveGrading('coarse', theForm, num);
}

function saveFineGrading(theForm,num) {
    saveGrading('fine', theForm, num);
}

function saveGrading(aggregateType, theForm, num) {
    var action = 'save_'+ aggregateType + '_aggregate' + num + '_grading';
    updateGrading(aggregateType, theForm, num);
    var action = 'save_'+ aggregateType + '_aggregate' + num + '_grading';
    var params = Form.serialize(theForm);

    new Ajax.Request("/vcctl/operation/prepareMix.do?action="+action, {
        method:'post',
        parameters:params,
        onSuccess: function(transport) {
            calculateAggregateGradingMassFractionsSumOfType(aggregateType,theForm,num);
        }
    });
}

function checkCoarseAggregateGradingMaxDiam(theElement,num) {
    var str = 'coarse_aggregate' + num + '_grading-min_sieve_diameter_0';
    var elstr = 'coarse_aggregate' + num + '_grading_massfrac_0';
    var diamElem = $(str);
    // var diamValue = parseFloat(trim(diamElem.textContent));
    var diamValue = parseFloat(trim(diamElem.innerHTML));
    var value = parseFloat(theElement.value);
    var result = true;

    if((value<=diamValue) || (isNaN(value))){
        alert("Maximum diameter must be greater than " + diamValue + "mm");
        value = diamValue + 10.0;
        theElement.value = value;
        theElement.focus();
        result = false;
    }

    var theForm = theElement.form;
    if (parseFloat(theForm[elstr].value) > 0) {
        var xDim = parseFloat(theForm.concrete_x_dim.value);
        var minDim = xDim;
        var yDim = parseFloat(theForm.concrete_y_dim.value);
        if (yDim < minDim) {
            minDim = yDim;
        }
        var zDim = parseFloat(theForm.concrete_z_dim.value);
        if (zDim < minDim) {
            minDim = zDim;
        }
        minDim = value / SIZE_SAFETY_COEFFICIENT;
        var res = parseFloat(theForm.concrete_resolution.value);
        minDim *= (1.0/res);
        var roundedMinDim = Math.round(minDim);
        roundedMinDim *= res;

        theForm.concrete_x_dim.value = roundedMinDim.toFixed(2);
        theForm.concrete_y_dim.value = roundedMinDim.toFixed(2);
        theForm.concrete_z_dim.value = roundedMinDim.toFixed(2);
    }
    return result;
}

function checkFineAggregateGradingMaxDiam(theElement,num) {
    var str = 'fine_aggregate' + num + '_grading-min_sieve_diameter_0';
    var elstr = 'fine_aggregate' + num + '_grading_massfrac_0';

    var minDiamElem = $(str);
    // var minDiamValue = parseFloat(trim(minDiamElem.textContent));
    var minDiamValue = parseFloat(trim(minDiamElem.innerHTML));
    /* Why $$('my-class:last-of-type') returns an array and not a single element? Is it a Prototype bug? */
    var maxDiamElements = $$('.coarse_aggregate_grading-sieve_diameter:last-of-type');
    var maxDiamElem = maxDiamElements[maxDiamElements.length-1];
    // var maxDiamValue = parseFloat(trim(maxDiamElem.textContent));
    var maxDiamValue = parseFloat(trim(maxDiamElem.innerHTML));
    var value = parseFloat(theElement.value);
    var result = true;

    if((value<=minDiamValue) || (value>=maxDiamValue) || (isNaN(value))){
        alert("Maximum diameter must be greater than " + minDiamValue + "mm and lower than " + maxDiamValue + "mm");
        value = maxDiamValue;
        theElement.value= value;
        theElement.focus();
        result = false;
    }

    var theForm = theElement.form;
    if (parseFloat(theForm[elstr].value) > 0) {
        var xDim = parseFloat(theForm.concrete_x_dim.value);
        var minDim = xDim;
        var yDim = parseFloat(theForm.concrete_y_dim.value);
        if (yDim < minDim) {
            minDim = yDim;
        }
        var zDim = parseFloat(theForm.concrete_z_dim.value);
        if (zDim < minDim) {
            minDim = zDim;
        }
        minDim = value / SIZE_SAFETY_COEFFICIENT;
        var res = parseFloat(theForm.concrete_resolution.value);
        minDim *= (1.0/res);
        var roundedMinDim = Math.round(minDim);
        roundedMinDim *= res;
        theForm.concrete_x_dim.value = roundedMinDim.toFixed(2);
        theForm.concrete_y_dim.value = roundedMinDim.toFixed(2);
        theForm.concrete_z_dim.value = roundedMinDim.toFixed(2);
    }
    return result;
}

function onChangeCoarseGrading(theForm,num) {
    onChangeGrading('coarse',theForm,num);
    calculateAggregateGradingMassFractionsSumOfType('coarse',theForm,num);
}

function onChangeFineGrading(theForm,num) {
    onChangeGrading('fine',theForm,num);
    calculateAggregateGradingMassFractionsSumOfType('fine',theForm,num);
}

function onChangeGrading(aggregateType, theForm, num) {
    var action = 'check_'+ aggregateType + '_aggregate' + num + '_grading';
    var params = Form.serialize(theForm);
    var status = 0;

    new Ajax.Request("/vcctl/operation/prepareMix.do?action="+action, {
        method:'post',
        parameters:params,
        onSuccess: function(transport) {
            if (transport.responseText == "grading.not-compatible-with-system-size") {
                alert("This grading is not compatible with the system size. The selected grading will be set back to the previous one.");
                status = 1;
            }
        }
    });

    if (status == 0) {
        changeTheGrading(aggregateType,theForm,num);
        recalculateMaxConcreteSystemDimensions(theForm);
        recalculateMaxConcreteSystemResolution(theForm);
        adjustConcreteSystemSizeToResolution(theForm);
    }
}

function changeTheGrading(aggregateType, theForm, num) {
    var action = 'change_'+ aggregateType + '_aggregate' + num + '_grading';
    var params = Form.serialize(theForm);

    new Ajax.Request("/vcctl/operation/prepareMix.do?action="+action, {
        method:'post',
        parameters:params,
        onSuccess: function(transport) {
            calculateAggregateGradingMassFractionsSumOfType(aggregateType,theForm,num);
        }
    });

}

function onChangeCoarseAggregateGradingMassFrac(theElement,num) {
    onChangeAggregateGradingMassFrac("coarse",theElement,num);
}

function onChangeFineAggregateGradingMassFrac(theElement,num) {
    onChangeAggregateGradingMassFrac("fine",theElement,num);
}

function onChangeAggregateGradingMassFrac(aggregateType, theElement, num) {
    var theForm = theElement.form;
    checkFieldValue(theElement,'Mass fraction');

    if (!checkIfTheBiggestPresentSieveIsNotTooBig(theForm)) {
        theElement.value = "0.0";
        theElement.focus();
        return false;
    }

    if (!checkIfTheSmallestPresentSieveIsNotTooSmall(theForm)) {
        theElement.value = "0.0";
        theElement.focus();
        return false;
    }
    adjustConcreteSystemSizeToResolution(theForm);

    var totalOK = calculateAggregateGradingMassFractionsSumOfType(aggregateType,theForm,num);
    if (!totalOK) {
        theElement.value="0.0";
        theElement.focus();
        return false;
    }
    updateGrading(aggregateType,theForm,num);
    recalculateMaxConcreteSystemDimensions(theForm);
    recalculateMaxConcreteSystemResolution(theForm);
    adjustConcreteSystemSizeToResolution(theForm);
    return true;
}

function checkIfTheBiggestPresentSieveIsNotTooBig(theForm) {
    var value = getBiggestPresentSieveDiameter(theForm);
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var minDim = xDim;
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    if (yDim < minDim) {
        minDim = yDim;
    }
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    if (zDim < minDim) {
        minDim = zDim;
    }
    
    minDim = value/SIZE_SAFETY_COEFFICIENT;
    var res = parseFloat(theForm.concrete_resolution.value);
    minDim *= (1.0/res);
    var roundedMinDim = Math.round(minDim);
    roundedMinDim *= res;
    theForm.concrete_x_dim.value = roundedMinDim.toFixed(2);
    theForm.concrete_y_dim.value = roundedMinDim.toFixed(2);
    theForm.concrete_z_dim.value = roundedMinDim.toFixed(2);
    
    return true;
}

function checkIfTheSmallestPresentSieveIsNotTooSmall(theForm) {
    var value = getSmallestPresentSieveDiameter(theForm);
    // alert("checkIfTheSmallestPresentSieveIsNotTooSmall value = " + value);
    if (value > 0) {
        var resolution = parseFloat(theForm.concrete_resolution.value);
        var newres = value/RESOLUTION_SAFETY_COEFFICIENT;
        // alert("checkIfTheSmallestPresentSieveIsNotTooSmall newres = " + newres);
        theForm.concrete_resolution.value = newres.toFixed(2);
        adjustConcreteSystemSizeToResolution(theForm);
    }
    return true;
}

function recalculateMaxConcreteSystemDimensions(theForm) {
    var value = getBiggestPresentSieveDiameter(theForm);
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var minDim = xDim;
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    if (yDim < minDim) {
        minDim = yDim;
    }
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    if (zDim < minDim) {
        minDim = zDim;
    }
    minDim = value/SIZE_SAFETY_COEFFICIENT;
    var res = parseFloat(theForm.concrete_resolution.value);
    minDim *= (1.0/res);
    var roundedMinDim = Math.round(minDim);
    roundedMinDim *= res;
    theForm.concrete_x_dim.value = roundedMinDim.toFixed(2);
    theForm.concrete_y_dim.value = roundedMinDim.toFixed(2);
    theForm.concrete_z_dim.value = roundedMinDim.toFixed(2);
    
    return true;
}

function recalculateMaxConcreteSystemResolution(theForm) {
    var value = getSmallestPresentSieveDiameter(theForm);
    // alert("recalculateMaxConcreteSystemResolution value = " + value);
    var newres = value/RESOLUTION_SAFETY_COEFFICIENT;
    // alert("recalculateMaxConcreteSystemResolution newres = " + newres);
    theForm.concrete_resolution.value = newres.toFixed(2);
    adjustConcreteSystemSizeToResolution(theForm);
    return true;
}

/**
* Finds the biggest sieve for which the mass fraction > 0
**/
function getBiggestPresentSieveDiameter(theForm) {
    // let's start with the coarse aggregate
    var massFracFieldName;
    var massFraction01Elements = $$('.coarse_aggregate01_grading_massfrac');
    var massFraction02Elements = $$('.coarse_aggregate02_grading_massfrac');
    var biggest = 0.0;
    var i;
    var diamElement;

    if (theForm['add_coarse_aggregate01_checkbox'].checked) {
        for (i = 0; i < massFraction01Elements.length; i++) {
            massFracFieldName = 'coarse_aggregate01_grading_massfrac_' + i;
            if (parseFloat(theForm[massFracFieldName].value) > 0) {
                if (i == 0) {
                    if (biggest < parseFloat(theForm.coarse_aggregate01_grading_max_diam.value)) {
                        biggest = parseFloat(theForm.coarse_aggregate01_grading_max_diam.value);
                    }
                } else {
                    diamElement = $('coarse_aggregate01_grading-min_sieve_diameter_' + (i-1));
                    // return parseFloat(trim(diamElement.textContent));
                    if (biggest < parseFloat(trim(diamElement.innerHTML))) {
                        biggest = parseFloat(trim(diamElement.innerHTML));
                    }

                }
            }
        }
    }
    if (theForm['add_coarse_aggregate02_checkbox'].checked) {
        for (i = 0; i < massFraction02Elements.length; i++) {
            massFracFieldName = 'coarse_aggregate02_grading_massfrac_' + i;
            if (parseFloat(theForm[massFracFieldName].value) > 0) {
                if (i == 0) {
                    if (biggest < parseFloat(theForm.coarse_aggregate02_grading_max_diam.value)) {
                        biggest = parseFloat(theForm.coarse_aggregate02_grading_max_diam.value);
                    }
                } else {
                    diamElement = $('coarse_aggregate02_grading-min_sieve_diameter_' + (i-1));
                    // return parseFloat(trim(diamElement.textContent));
                    if (biggest < parseFloat(trim(diamElement.innerHTML))) {
                        biggest = parseFloat(trim(diamElement.innerHTML));
                    }
                }
            }
        }
    }

    if (biggest > 0.0) {
        return biggest;
    } else {

        if (theForm['add_fine_aggregate01_checkbox'].checked) {

            // if no sieve has a mass fraction > 0 for coarse aggregate, let's try with fine aggregate
            massFraction01Elements = $$('.fine_aggregate01_grading_massfrac');
            massFraction02Elements = $$('.fine_aggregate02_grading_massfrac');

            for (i = 0; i < massFraction01Elements.length; i++) {
                massFracFieldName = 'fine_aggregate01_grading_massfrac_' + i;
                if (parseFloat(theForm[massFracFieldName].value) > 0) {
                    if (i == 0) {
                        if (biggest < parseFloat(theForm.fine_aggregate01_grading_max_diam.value)) {
                            biggest = parseFloat(theForm.fine_aggregate01_grading_max_diam.value);
                        }
                    } else {
                        diamElement = $('fine_aggregate01_grading-min_sieve_diameter_' + (i-1));
                        // return parseFloat(trim(diamElement.textContent));
                        if (biggest < parseFloat(trim(diamElement.innerHTML))) {
                            biggest = parseFloat(trim(diamElement.innerHTML));
                        }
                    }
                }
            }
        }
        if (theForm['add_fine_aggregate02_checkbox'].checked) {

            for (i = 0; i < massFraction02Elements.length; i++) {
                massFracFieldName = 'fine_aggregate02_grading_massfrac_' + i;
                if (parseFloat(theForm[massFracFieldName].value) > 0) {
                    if (i == 0) {
                        if (biggest < parseFloat(theForm.fine_aggregate02_grading_max_diam.value)) {
                            biggest = parseFloat(theForm.fine_aggregate02_grading_max_diam.value);
                        }
                    } else {
                        diamElement = $('fine_aggregate02_grading-min_sieve_diameter_' + (i-1));
                        // return parseFloat(trim(diamElement.textContent));
                        if (biggest < parseFloat(trim(diamElement.innerHTML))) {
                            biggest = parseFloat(trim(diamElement.innerHTML));
                        }
                    }
                }
            }
        }
        return biggest;
    }
    return biggest;
}

/*
* Finds the smallest sieve for which the mass fraction > 0
**/
function getSmallestPresentSieveDiameter(theForm) {
    // let's start with the fine aggregate
    var massFracFieldName;
    var diamElement;
    var i;
    var massFraction01Elements = $$('.fine_aggregate01_grading_massfrac');
    var massFraction02Elements = $$('.fine_aggregate02_grading_massfrac');
    var smallest = 1000000.0;

    if (theForm['add_fine_aggregate01_checkbox'].checked) {
        // alert("Fine Aggregate 01 is checked, length is " + massFraction01Elements.length);
        for (i = massFraction01Elements.length; i > 0; i--) {
            massFracFieldName = 'fine_aggregate01_grading_massfrac_' + (i - 1);
            if (parseFloat(theForm[massFracFieldName].value) > 0) {
                diamElement = $('fine_aggregate01_grading-min_sieve_diameter_' + (i-1));
                // return parseFloat(trim(diamElement.textContent));
                if (smallest > parseFloat(trim(diamElement.innerHTML))) {
                    smallest = parseFloat(trim(diamElement.innerHTML));
                }

            }
        }
        // alert("Smallest in Fine Aggregate 01 = " + smallest);
    }
    if (theForm['add_fine_aggregate02_checkbox'].checked) {
        // alert("Fine Aggregate 02 is checked, length is " + massFraction02Elements.length);
        for (i = massFraction02Elements.length; i > 0; i--) {
            massFracFieldName = 'fine_aggregate02_grading_massfrac_' + (i - 1);
            if (parseFloat(theForm[massFracFieldName].value) > 0) {
                diamElement = $('fine_aggregate02_grading-min_sieve_diameter_' + (i-1));
                // return parseFloat(trim(diamElement.textContent));
                if (smallest > parseFloat(trim(diamElement.innerHTML))) {
                    smallest = parseFloat(trim(diamElement.innerHTML));
                }

            }
        }
        // alert("Smallest in Fine Aggregate 01 = " + smallest);
    }

    if (smallest < 1000000.0) {
        // alert("Returning control to jsp page now");
        return smallest;
    } else {

        // if no sieve has a mass fraction > 0 for fine aggregate, let's try with coarse aggregate
        massFraction01Elements = $$('.coarse_aggregate01_grading_massfrac');
        massFraction02Elements = $$('.coarse_aggregate02_grading_massfrac');
        if (theForm['add_coarse_aggregate01_checkbox'].checked) {
            for (i = massFraction01Elements.length; i > 0; i--) {
                massFracFieldName = 'coarse_aggregate01_grading_massfrac_' + (i - 1);
                if (parseFloat(theForm[massFracFieldName].value) > 0) {
                    diamElement = $('coarse_aggregate01_grading-min_sieve_diameter_' + (i-1));
                     // return parseFloat(trim(diamElement.textContent));
                    if (smallest > parseFloat(trim(diamElement.innerHTML))) {
                        smallest = parseFloat(trim(diamElement.innerHTML));
                    }
                }
            }
        }
        if (theForm['add_coarse_aggregate02_checkbox'].checked) {
            for (i = massFraction02Elements.length; i > 0; i--) {
                massFracFieldName = 'coarse_aggregate02_grading_massfrac_' + (i - 1);
                if (parseFloat(theForm[massFracFieldName].value) > 0) {
                    diamElement = $('coarse_aggregate02_grading-min_sieve_diameter_' + (i-1));
                     // return parseFloat(trim(diamElement.textContent));
                    if (smallest > parseFloat(trim(diamElement.innerHTML))) {
                        smallest = parseFloat(trim(diamElement.innerHTML));
                    }
                }
            }
        }
        if (smallest < 1000000.0) {
            return smallest;
        } else {
            return 0.0
        }
    }
    return 0;
}

function updateGrading(aggregateType, theForm, num) {
    // alert("In updateGrading now");
    var grading = "Sieve\tDiam\tMass_frac\n";
    var rootID = aggregateType + '_aggregate' + num + '_properties-content';
    var gradingLinesClassName = aggregateType + '_aggregate' + num + '_grading-line';
    // var gradingLines = $(rootID).getElementsByClassName(gradingLinesClassName);
    var gradingLines = $(rootID).select('.' + gradingLinesClassName);
    var elementClassName, element, elementValue, massFracFieldName, massFrac;
    for (var i=0; i<gradingLines.length;i++) {
        /* Sieve name */
        elementID = aggregateType + '_aggregate' + num + '_grading-sieve_name_' + i;
        element = $(elementID);
        // elementValue = trim(element.textContent);
        elementValue = trim(element.innerHTML);
        grading = grading + elementValue + "\t";
        /* Sieve diameter */
        elementID = aggregateType + '_aggregate' + num + '_grading-min_sieve_diameter_' + i;
        element = $(elementID);
        // elementValue = trim(element.textContent);
        elementValue = trim(element.innerHTML);
        grading = grading + elementValue + "\t";
        /* Mass fraction */
        massFracFieldName = aggregateType + '_aggregate' + num + '_grading_massfrac_' + i;
        massFrac = theForm[massFracFieldName].value;
        grading = grading + massFrac + "\n";
    }
    var gradingName = aggregateType + '_aggregate' + num + '_grading';
    theForm[gradingName].value = grading;
    // alert("Finished updateGrading now");
}

function calculateAggregateGradingMassFractionsSumOfType(aggregateType, theForm, num) {
    var rootID = aggregateType + '_aggregate' + num + '_properties-content';
    var gradingLinesClassName = aggregateType + '_aggregate' + num + '_grading-line';
    var gradingLines = $(rootID).getElementsByClassName(gradingLinesClassName);
    // var gradingLines = $(rootID).$$('.' + gradingLinesClassName);
    var massFracFieldName, massFrac;
    var totalMassFrac = 0.0;
    for (var i=0; i<gradingLines.length;i++) {
        massFracFieldName = aggregateType + '_aggregate' + num + '_grading_massfrac_' + i;
        massFrac = theForm[massFracFieldName].value;
        totalMassFrac += parseFloat(massFrac);
    }
    
    var totalMassFracFieldName = aggregateType + '_aggregate' + num + '_grading_total_massfrac';
    theForm[totalMassFracFieldName].value = totalMassFrac.toNiceFixed(4);
    return true;
}

function addOrRemoveCoarseAggregate(theForm,num) {
    addOrRemoveAggregate('coarse', theForm,num);
}

function addOrRemoveFineAggregate(theForm,num) {
    addOrRemoveAggregate('fine', theForm,num);
}

function addOrRemoveAggregate(aggregateType, theForm, num) {
    var massFracField = aggregateType + '_aggregate' + num + '_massfrac';
    var volFracField = aggregateType + '_aggregate' + num + '_volfrac';
    var checkBoxName = 'add_' + aggregateType + '_aggregate' + num + '_checkbox';
    var useAggregateField = 'add_' + aggregateType + '_aggregate' + num;
    var frac;
    var index = aggregateType + num;

    theForm[useAggregateField].value = theForm[checkBoxName].checked;

    if (theForm[checkBoxName].checked) {
        enableOrDisableAggregateLine(true,theForm,aggregateType,num);
        frac = savedMassFractions[index];
        if (frac > 0) {
            theForm[massFracField].value = frac.toNiceFixed(4);
        }
        frac = savedVolumeFractions[index];
        if (frac > 0) {
            theForm[volFracField].value = frac.toNiceFixed(4);
        }
    }
    else {
        enableOrDisableAggregateLine(false,theForm,aggregateType,num);
        frac = parseFloat(theForm[massFracField].value);
        savedMassFractions[index] = frac;
        theForm[massFracField].value = "0.0";

        frac = parseFloat(theForm[volFracField].value);
        savedVolumeFractions[index] = frac;
        theForm[volFracField].value = "0.0";
    }

    var totalAggregateMassFrac = parseFloat(theForm['coarse_aggregate01_massfrac'].value) + parseFloat(theForm['fine_aggregate01_massfrac'].value);
    totalAggregateMassFrac += parseFloat(theForm['coarse_aggregate02_massfrac'].value) + parseFloat(theForm['fine_aggregate02_massfrac'].value);

    var waterBinderRatio = parseFloat(theForm['water_binder_ratio'].value);

    var newBinderMassFrac = (1 / (waterBinderRatio + 1)) * (1 - totalAggregateMassFrac);
    var newWaterMassFrac = (waterBinderRatio / (waterBinderRatio + 1)) * (1 - totalAggregateMassFrac);

    theForm['binder_massfrac'].value = newBinderMassFrac.toNiceFixed(4);
    theForm['water_massfrac'].value = newWaterMassFrac.toNiceFixed(4);

    updateMixVolumeFractions(theForm);
    hideOrDisplayAirVolumeFraction(theForm);
    hideOrDisplayConcreteSystemSize(theForm);
    onAddAggregateCheckSystemSize(theForm);
    // alert("Before onAddAggregateCheckSystemResolution, res = " + theForm.concrete_resolution.value);
    onAddAggregateCheckSystemResolution(theForm);
    // alert("After onAddAggregateCheckSystemResolution, res = " + theForm.concrete_resolution.value);
    adjustConcreteSystemSizeToResolution(theForm);
    // alert("After adjustConcreteSystemSizeToResolution, res = " + theForm.concrete_resolution.value);
}

function hideOrDisplayAirVolumeFraction(theForm) {
    if (theForm['add_coarse_aggregate01_checkbox'].checked || theForm['add_fine_aggregate01_checkbox'].checked || theForm['add_coarse_aggregate02_checkbox'].checked || theForm['add_fine_aggregate02_checkbox'].checked) {
        display('air_line');
    } else {
        hide('air_line');
    }
}

function hideOrDisplayConcreteSystemSize(theForm) {
    if (theForm['add_coarse_aggregate01_checkbox'].checked || theForm['add_fine_aggregate01_checkbox'].checked || theForm['add_coarse_aggregate02_checkbox'].checked || theForm['add_fine_aggregate02_checkbox'].checked) {
        display('concrete_system_size_table');
    } else {
        hide('concrete_system_size_table');
    }
}

function enableOrDisableVisualizeConcrete(theForm) {
    if (theForm['add_coarse_aggregate01_checkbox'].checked || theForm['add_fine_aggregate01_checkbox'].checked || theForm['add_coarse_aggregate02_checkbox'].checked || theForm['add_fine_aggregate02_checkbox'].checked) {
        theForm['use_visualize_concrete_checkbox'].disabled = false;
    } else {
        theForm['use_visualize_concrete_checkbox'].disabled = true;
    }
}

function enableOrDisableAggregateLine(enable,theForm,aggregateType,num) {
    var divID = aggregateType + '_aggregate' + num + '_properties';
    var massFracField = aggregateType + '_aggregate' + num + '_massfrac';
    var volumeFracField = aggregateType + '_aggregate' + num + '_volfrac';
    var checkBoxName = 'add_' + aggregateType + '_aggregate' + num + '_checkbox';
    var useAggregateField = 'add_' + aggregateType + '_aggregate' + num;
    theForm[checkBoxName].checked = enable;
    theForm[useAggregateField].value = enable;
    theForm[massFracField].disabled = (!enable);
    theForm[volumeFracField].disabled = (!enable);
    hideOrDisplay(divID);
}

/**
* Update binder, coarse aggregate, fine aggregate and water volume fraction
**/
function updateMixVolumeFractions(theForm) {
    var sumVolume = 0.0;

    updateBinderSpecificGravity(theForm);

    /* Binder */
    var binderMassFraction = checkAndGetValueOfField(theForm.binder_massfrac,"The mass fraction of the binder");
    var binderSpecificGravity = parseFloat(theForm.binder_sg.value);
    var binderVolume = binderMassFraction/binderSpecificGravity;
    sumVolume = sumVolume + binderVolume;

    var mfi;
    var coarseAggregate01SpecificGravity,coarseAggregate02SpecificGravity;
    var coarseAggregate01Volume,coarseAggregate02Volume;
    var fineAggregate01SpecificGravity,fineAggregate02SpecificGravity;
    var fineAggregate01Volume,fineAggregate02Volume;

    if (theForm['add_coarse_aggregate01_checkbox'].checked) {

        /* Coarse aggregate 01 */
        var mfi = checkAndGetValueOfField(theForm.coarse_aggregate01_massfrac,"The mass fraction of the coarse aggregate01");
        var coarseAggregate01SpecificGravity = parseFloat(theForm.coarse_aggregate01_sg.value);
        var coarseAggregate01Volume = mfi/coarseAggregate01SpecificGravity;
        sumVolume = sumVolume + coarseAggregate01Volume;
    } else {
        coarseAggregate01Volume = 0.0;
    }

    if (theForm['add_coarse_aggregate02_checkbox'].checked) {

        /* Coarse aggregate 02 */
        mfi = checkAndGetValueOfField(theForm.coarse_aggregate01_massfrac,"The mass fraction of the coarse aggregate02");
        coarseAggregate02SpecificGravity = parseFloat(theForm.coarse_aggregate02_sg.value);
        coarseAggregate02Volume = mfi/coarseAggregate02SpecificGravity;
        sumVolume = sumVolume + coarseAggregate02Volume;
    } else {
        coarseAggregate02Volume = 0.0;
    }

    if (theForm['add_fine_aggregate01_checkbox'].checked) {

        /* Fine aggregate 01*/
        mfi = checkAndGetValueOfField(theForm.fine_aggregate01_massfrac,"The mass fraction of the fine aggregate01");
        fineAggregate01SpecificGravity = parseFloat(theForm.fine_aggregate01_sg.value);
        fineAggregate01Volume = mfi/fineAggregate01SpecificGravity;
        sumVolume = sumVolume + fineAggregate01Volume;
    } else {
        fineAggregate01Volume = 0.0;
    }

    if (theForm['add_fine_aggregate02_checkbox'].checked) {

        /* Fine aggregate 02*/
        mfi = checkAndGetValueOfField(theForm.fine_aggregate02_massfrac,"The mass fraction of the fine aggregate02");
        fineAggregate02SpecificGravity = parseFloat(theForm.fine_aggregate02_sg.value);
        fineAggregate02Volume = mfi/fineAggregate02SpecificGravity;
        sumVolume = sumVolume + fineAggregate02Volume;
    } else {
        fineAggregate02Volume = 0.0;
    }

    /* Water */
    mfi = checkAndGetValueOfField(theForm.water_massfrac,"The mass fraction of the water");
    var waterVolume = mfi/WATER_DENSITY;
    sumVolume = sumVolume + waterVolume;

    // Set water/solid ratio
    theForm.water_binder_ratio.value = (mfi/binderMassFraction).toNiceFixed(3);

    var volumeFraction = binderVolume/sumVolume;
    theForm.binder_volfrac.value=volumeFraction.toNiceFixed(4);
    volumeFraction = coarseAggregate01Volume/sumVolume;
    theForm.coarse_aggregate01_volfrac.value=volumeFraction.toNiceFixed(4);
    volumeFraction = coarseAggregate02Volume/sumVolume;
    theForm.coarse_aggregate02_volfrac.value=volumeFraction.toNiceFixed(4);
    volumeFraction = fineAggregate01Volume/sumVolume;
    theForm.fine_aggregate01_volfrac.value=volumeFraction.toNiceFixed(4);
    volumeFraction = fineAggregate02Volume/sumVolume;
    theForm.fine_aggregate02_volfrac.value=volumeFraction.toNiceFixed(4);
    volumeFraction = waterVolume/sumVolume;
    theForm.water_volfrac.value=volumeFraction.toNiceFixed(4);
}

function updateMixMassFractions(theForm) {
    /* Update binder, coarse aggregate, fine aggregate and water volume fraction*/
    var sumMass = 0.0;

    updateBinderSpecificGravity(theForm);

    /* Binder */
    var vfi = checkAndGetValueOfField(theForm.binder_volfrac,"The volume fraction of the binder");
    var binderSpecificGravity = parseFloat(theForm.binder_sg.value);
    var binderMass = vfi*binderSpecificGravity;
    sumMass = sumMass + binderMass;

    var coarseAggregate01SpecificGravity,coarseAggregate02SpecificGravity;
    var coarseAggregate01Mass,coarseAggregate02Mass;
    var fineAggregate01SpecificGravity,fineAggregate02SpecificGravity;
    var fineAggregate01Mass,fineAggregate02Mass;

    if (theForm['add_coarse_aggregate01_checkbox'].checked) {

        /* Coarse aggregate 01 */
        vfi = checkAndGetValueOfField(theForm.coarse_aggregate01_volfrac,"The volume fraction of the coarse aggregate01");
        coarseAggregate01SpecificGravity = parseFloat(theForm.coarse_aggregate01_sg.value);
        coarseAggregate01Mass = vfi*coarseAggregate01SpecificGravity;
        sumMass = sumMass + coarseAggregate01Mass;
    } else {
        coarseAggregate01Mass = 0.0;
    }

    if (theForm['add_coarse_aggregate02_checkbox'].checked) {

        /* Coarse aggregate 02 */
        vfi = checkAndGetValueOfField(theForm.coarse_aggregate02_volfrac,"The volume fraction of the coarse aggregate01");
        coarseAggregate02SpecificGravity = parseFloat(theForm.coarse_aggregate02_sg.value);
        coarseAggregate02Mass = vfi*coarseAggregate02SpecificGravity;
        sumMass = sumMass + coarseAggregate02Mass;
    } else {
        coarseAggregate02Mass = 0.0;
    }

    if (theForm['add_fine_aggregate01_checkbox'].checked) {

        /* Fine aggregate 01 */
        vfi = checkAndGetValueOfField(theForm.fine_aggregate01_volfrac,"The volume fraction of the fine aggregate01");
        fineAggregate01SpecificGravity = parseFloat(theForm.fine_aggregate01_sg.value);
        fineAggregate01Mass = vfi*fineAggregate01SpecificGravity;
        sumMass = sumMass + fineAggregate01Mass;
    } else {
        fineAggregate01Mass = 0.0;
    }

    if (theForm['add_fine_aggregate02_checkbox'].checked) {

        /* Fine aggregate 02 */
        vfi = checkAndGetValueOfField(theForm.fine_aggregate02_volfrac,"The volume fraction of the fine aggregate02");
        fineAggregate02SpecificGravity = parseFloat(theForm.fine_aggregate02_sg.value);
        fineAggregate02Mass = vfi*fineAggregate02SpecificGravity;
        sumMass = sumMass + fineAggregate02Mass;
    } else {
        fineAggregate02Mass = 0.0;
    }

    /* Water */
    vfi = checkAndGetValueOfField(theForm.water_volfrac,"The volume fraction of the water");
    var waterMass = vfi*WATER_DENSITY;
    sumMass = sumMass + waterMass;

    // Set water/solid ratio
    theForm.water_binder_ratio.value = (waterMass/binderMass).toNiceFixed(3);

    var massFraction = binderMass/sumMass;
    theForm.binder_massfrac.value=massFraction.toNiceFixed(4);
    massFraction = coarseAggregate01Mass/sumMass;
    theForm.coarse_aggregate01_massfrac.value=massFraction.toNiceFixed(4);
    massFraction = coarseAggregate02Mass/sumMass;
    theForm.coarse_aggregate02_massfrac.value=massFraction.toNiceFixed(4);
    massFraction = fineAggregate01Mass/sumMass;
    theForm.fine_aggregate01_massfrac.value=massFraction.toNiceFixed(4);
    massFraction = fineAggregate02Mass/sumMass;
    theForm.fine_aggregate02_massfrac.value=massFraction.toNiceFixed(4);
    massFraction = waterMass/sumMass;
    theForm.water_massfrac.value=massFraction.toNiceFixed(4);
}

/*
* Simulation parameters functions
*/

var savedRandomSeed;

function useOwnRandomSeed(checkBox) {
    var theForm = checkBox.form;
    var enable = checkBox.checked;
    theForm.use_own_random_seed.value = enable;
    theForm.rng_seed.disabled = !enable;
    if (enable && savedRandomSeed != null && savedRandomSeed != 0) {
        theForm.rng_seed.value = savedRandomSeed;
    } else {
        savedRandomSeed = theForm.rng_seed.value;
        theForm.rng_seed.value = 0;
    }
}

var savedShapeSetID;

function useRealParticleShapes(checkBox) {
    var theForm = checkBox.form;
    var enable = checkBox.checked;
    theForm.shape_set.disabled = !enable;
    if (!enable) {
        savedShapeSetID = theForm.shape_set.selectedIndex;
        theForm.shape_set.selectedIndex = 0;
    } else if (savedShapeSetID != null && savedShapeSetID > 0) {
        theForm.shape_set.selectedIndex = savedShapeSetID;
    } else {
        theForm.shape_set.selectedIndex = 1;
    }
    theForm.real_shapes.value = enable;
}

var savedFlocculation;

function useFlocculation(checkBox) {
    var theForm = checkBox.form;
    var enable = checkBox.checked;
    theForm.use_flocculation.value = enable;
    theForm.flocdegree.disabled = !enable;
    if (enable) {
        theForm.use_dispersion_distance_checkbox.checked = !enable;
        theForm.use_dispersion_distance.value = !enable;
        theForm.dispersion_distance.disabled = enable;
        savedDispersionDistanceID = theForm.dispersion_distance.selectedIndex;
        theForm.dispersion_distance.selectedIndex = 0;
        if (savedFlocculation != null && savedFlocculation != 0) {
            theForm.flocdegree.value = savedFlocculation;
        }
    } else {
        savedFlocculation = theForm.flocdegree.value;
        theForm.flocdegree.value  = 0;
    }
}

var savedDispersionDistanceID;

function useDispersionDistance(checkBox) {
    var theForm = checkBox.form;
    var enable = checkBox.checked;
    theForm.use_dispersion_distance.value = enable;
    theForm.dispersion_distance.disabled = !enable;
    if (enable) {
        theForm.use_flocculation_checkbox.checked = !enable;
        theForm.use_flocculation.value = !enable;
        theForm.flocdegree.disabled = enable;
        savedFlocculation = theForm.flocdegree.value;
        theForm.flocdegree.value = 0;
        if (savedDispersionDistanceID != null && savedDispersionDistanceID > 0) {
            theForm.dispersion_distance.selectedIndex = savedDispersionDistanceID;
        } else {
            theForm.dispersion_distance.selectedIndex = 1;
        }
    } else {
        savedDispersionDistanceID = theForm.dispersion_distance.selectedIndex;
        theForm.dispersion_distance.selectedIndex = 0;
    }
}

function useVisualizeConcrete(checkBox) {
    var theForm = checkBox.form;
    var enable = checkBox.checked;
    theForm.use_visualize_concrete.value = enable;
    if (theForm.use_visualize_concrete_checkbox.checked == true) {
        var xDim = parseFloat(theForm.concrete_x_dim.value);
        var yDim = parseFloat(theForm.concrete_y_dim.value);
        var zDim = parseFloat(theForm.concrete_z_dim.value);
        var resolution = parseFloat(theForm.concrete_resolution.value);
        var newres,roundedNewRes;
        var totpix = (xDim * yDim * zDim / resolution / resolution / resolution);
        if (totpix > MAX_PIXELS_ERROR) {
           alert("The concrete system must have less than " + MAX_PIXELS_ERROR + " pixels.  Adjusting resolution to reduce pixels.");
           newres = Math.pow(((xDim * yDim * zDim)/(0.5 * MAX_PIXELS_WARNING)),0.3333333);
           newres *= 100.00;
           roundedNewRes = Math.round(newres);
           roundedNewRes /= 100.00;
           theForm.concrete_resolution.value = roundedNewRes.toFixed(2);
        }
        if (totpix > MAX_PIXELS_WARNING) {
           alert("WARNING: With your settings, the concrete system  will have " + totpix + " pixels.  This could take a long time to make");
        }
    }
    return true;
}

function onChangeParticleShape(popupMenu) {
    if (popupMenu.selectedIndex == 0) { // If the user selected "None"
        popupMenu.form.real_shapes.value = false;
        popupMenu.form.shape_set.disabled = true;
        popupMenu.form.real_shapes_checkbox.checked = false;
    }
}

function onChangeDispersionDistance(popupMenu) {
    if (popupMenu.selectedIndex == 0) { // If the user selected "None"
        popupMenu.form.use_dispersion_distance.value = false;
        popupMenu.form.dispersion_distance.disabled = true;
        popupMenu.form.use_dispersion_distance_checkbox.checked = false;
    }
}

function onChangeConcreteSystemSize(theElement) {
    theForm = theElement.form;
    var dimension;
    var maxParticleDiameter;
    var newres,roundedNewRes;
    var newValue = parseFloat(theElement.value);
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    var resolution = parseFloat(theForm.concrete_resolution.value);
    var totpix = (xDim * yDim * zDim / resolution / resolution / resolution);
    if (newValue <= 0) {
        newValue = 1;
        theElement.value = newValue;
    }
    if (totpix > MAX_PIXELS_ERROR) {
       if (theForm.use_visualize_concrete_checkbox.checked == true) {
           alert("The concrete system must have less than " + MAX_PIXELS_ERROR + " pixels.  Adjusting resolution to reduce pixels.");
       }
       newres = Math.pow(((xDim * yDim * zDim)/(0.5 * MAX_PIXELS_WARNING)),0.3333333);
       newres *= 100.00;
       roundedNewRes = Math.round(newres);
       roundedNewRes /= 100.00;
       theForm.concrete_resolution.value = roundedNewRes.toFixed(2);
       return false;
    }
    if (totpix > MAX_PIXELS_WARNING) {
        if (theForm.use_visualize_concrete_checkbox.checked == true) {
            alert("WARNING: With your settings, the concrete system  will have " + totpix + " pixels.  This could take a long time to make.");
        }
    }

    maxParticleDiameter = getBiggestPresentSieveDiameter(theForm);
    if (maxParticleDiameter > 0) {
        dimension = parseFloat(theElement.value);
        if (maxParticleDiameter > (SIZE_SAFETY_COEFFICIENT * dimension)) {
            if (theForm.use_visualize_concrete_checkbox.checked == true) {
                alert("The dimension must be "+ (((1 / SIZE_SAFETY_COEFFICIENT)) * 100).toNiceFixed(1) +"% greater than the biggest aggregate particle.");
            }
            theElement.value = maxParticleDiameter / SIZE_SAFETY_COEFFICIENT;
            adjustConcreteSystemSizeToResolution(theForm);
            theElement.focus();
            return false;
        }
    }
    adjustConcreteSystemSizeToResolution(theForm);
    return true;

}

function onChangeConcreteSystemResolution(theElement) {
    theForm = theElement.form;
    var resolution = parseFloat(theElement.value);
    var newres,roundedNewRes;
    var minParticleDiameter;
    var totpix;
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    if (resolution <= 0.0) {
        resolution = 0.01;
        theElement.value = resolution.toFixed(2);
    }
    // minParticleDiameter = getSmallestPresentSieveDiameter(theForm);
    // if (minParticleDiameter > 0) {
    //     resolution = parseFloat(theForm.concrete_resolution.value);
    //     if (minParticleDiameter < (RESOLUTION_SAFETY_COEFFICIENT * resolution)) {
    //         if (theForm.use_visualize_concrete_checkbox.checked == true) {
    //             alert("The resolution must be "+ RESOLUTION_SAFETY_COEFFICIENT.toNiceFixed(1) + " times smaller than the smallest aggregate particle.");
    //         }
    //         newres = parseFloat(minParticleDiameter/RESOLUTION_SAFETY_COEFFICIENT);
    //         theElement.value = newres.toFixed(2);
    //         theElement.focus();
    //         return false;
    //     }
    // }
    totpix = (xDim * yDim * zDim / resolution / resolution / resolution);
    if ((totpix) > MAX_PIXELS_ERROR) {
       if (theForm.use_visualize_concrete_checkbox.checked == true) {
           alert("The concrete system must have less than " + MAX_PIXELS_ERROR + " pixels.  Adjusting resolution to reduce pixels.");
       }
       newres = Math.pow(((xDim * yDim * zDim)/(0.5 * MAX_PIXELS_WARNING)),0.3333333);
       newres *= 100.00;
       roundedNewRes = Math.round(newres);
       roundedNewRes /= 100.00;
       theElement.value = roundedNewRes.toFixed(2);
       return false;
    }
    if ((totpix) > MAX_PIXELS_WARNING) {
        if (theForm.use_visualize_concrete_checkbox.checked == true) {
            alert("WARNING: With your settings, the concrete system  will have " + totpix.toString() + " pixels.  This could take a long time to make.");
        }
    }
    adjustConcreteSystemSizeToResolution(theForm);
    return true;

}

function onAddAggregateCheckSystemSize(theForm) {
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    var maxParticleDiameter = parseFloat(getBiggestPresentSieveDiameter(theForm));
    if (maxParticleDiameter > 0) {
        var minDim = parseFloat(xDim);
        if (yDim < minDim) minDim = parseFloat(yDim);
        if (zDim < minDim) minDim = parseFloat(zDim);
        minDim = parseFloat((maxParticleDiameter / SIZE_SAFETY_COEFFICIENT)+0.5);
        var res = parseFloat(theForm.concrete_resolution.value);
        minDim *= (1.0/res);
        var roundedMinDim = Math.round(minDim);
        roundedMinDim *= res;
        theForm.concrete_z_dim.value = roundedMinDim.toFixed(2);
        theForm.concrete_y_dim.value = roundedMinDim.toFixed(2);
        theForm.concrete_x_dim.value = roundedMinDim.toFixed(2);
    }

    return true;
}

function onAddAggregateCheckSystemResolution(theForm) {
    var resolution = parseFloat(theForm.concrete_resolution.value);
    if (resolution <= 0) {
        resolution = 0.01;
        theForm.concrete_resolution.value = "0.01";
    }
    resolution = parseFloat(theForm.concrete_resolution.value);
    var newres;
    var roundedNewRes;
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    var totpix = (xDim * yDim * zDim / resolution / resolution / resolution);

    var minParticleDiameter = getSmallestPresentSieveDiameter(theForm);
    // alert("onAddAggregateCheckSystemResolution minParticleDiameter = " + minParticleDiameter);
    if (minParticleDiameter > 0) {
        newres = parseFloat(minParticleDiameter/RESOLUTION_SAFETY_COEFFICIENT);
        // alert("newres = " + newres);
        newres *= 100.00;
        // alert("100 newres = " + newres);
        roundedNewRes = Math.round(newres);
        // alert("Rounded newres = " + roundedNewRes);
        roundedNewRes /= 100.00;
        // alert("Rounded newres/100 = " + roundedNewRes);
        theForm.concrete_resolution.value = roundedNewRes.toFixed(2);
    }
    resolution = parseFloat(theForm.concrete_resolution.value);
    // alert("onAddAggregateCheckSystemResolution says that resolution = " + resolution);
    totpix = (xDim * yDim * zDim / resolution / resolution / resolution);
    if ((totpix) > MAX_PIXELS_ERROR) {
        if (theForm.use_visualize_concrete_checkbox.checked == true) {
           alert("The concrete system must have less than " + MAX_PIXELS_ERROR + " pixels.  Adjusting resolution to reduce pixels.");
       }
       newres = Math.pow(((xDim * yDim * zDim)/(0.5 * MAX_PIXELS_WARNING)),0.3333333);
       newres *= 100.00;
       roundedNewRes = Math.round(newres);
       roundedNewRes /= 100.00;
       theForm.concrete_resolution.value = roundedNewRes.toFixed(2);
    }
    resolution = parseFloat(theForm.concrete_resolution.value);
    totpix = (xDim * yDim * zDim / resolution / resolution / resolution);
    if ((totpix) > MAX_PIXELS_WARNING) {
        if (theForm.use_visualize_concrete_checkbox.checked == true) {
            alert("WARNING: With your settings, the concrete system  will have " + totpix.toString() + " pixels.  This could take a long time to make.");
        }

    }
    return true;
}

function adjustConcreteSystemSizeToResolution(theForm) {
    var xDim = parseFloat(theForm.concrete_x_dim.value);
    var yDim = parseFloat(theForm.concrete_y_dim.value);
    var zDim = parseFloat(theForm.concrete_z_dim.value);
    var res = parseFloat(theForm.concrete_resolution.value);
    var resMultiples = parseInt(xDim/res + 0.5);
    xDim = res * resMultiples;
    xDim *= 100.00;
    var roundedXDim =  Math.round(xDim);
    roundedXDim /= 100.0;
    resMultiples = parseInt(yDim/res + 0.5);
    yDim = res * resMultiples;
    yDim *= 100.00;
    var roundedYDim =  Math.round(yDim);
    roundedYDim /= 100.0;
    resMultiples = parseInt(zDim/res + 0.5);
    zDim = res * resMultiples;
    zDim *= 100.00;
    var roundedZDim =  Math.round(zDim);
    roundedZDim /= 100.0;

    theForm.concrete_x_dim.value = roundedXDim.toFixed(2);
    theForm.concrete_y_dim.value = roundedYDim.toFixed(2);
    theForm.concrete_z_dim.value = roundedZDim.toFixed(2);

    return true;

}

function onChangeBinderSystemSize(theElement) {
    theForm = theElement.form;
    var newValue = parseFloat(theElement.value);
    if (newValue <= 0) {
        newValue = 1;
        theElement.value = "1";
    }
    var xDim = parseFloat(theForm.binder_x_dim.value);
    var yDim = parseFloat(theForm.binder_y_dim.value);
    var zDim = parseFloat(theForm.binder_z_dim.value);
    var resolution = parseFloat(theForm.binder_resolution.value);
    if ((xDim * yDim * zDim / resolution) > MAX_PIXELS_ERROR) {
        alert("The system must be less than " + MAX_PIXELS_ERROR + " pixels.");
        theElement.value = Math.floor(MAX_PIXELS_ERROR * resolution * newValue / (xDim * yDim * zDim));
        theElement.focus();
        return false;
    }
    
    return true;

}

function onChangeBinderSystemResolution(theElement) {
    theForm = theElement.form;
    var resolution = parseFloat(theElement.value);
    if (resolution <= 0) {
        resolution = 0.01;
        theElement.value = "0.01";
    }
    var xDim = parseFloat(theForm.binder_x_dim.value);
    var yDim = parseFloat(theForm.binder_y_dim.value);
    var zDim = parseFloat(theForm.binder_z_dim.value);
    if ((xDim * yDim * zDim / resolution) > MAX_PIXELS_ERROR) {
        alert("The system must be less than " + MAX_PIXELS_ERROR + " pixels.");
        theElement.value = Math.ceil((xDim * yDim * zDim / MAX_PIXELS_ERROR) * 100) / 100; // round to 2 digits after decimal separator
        theElement.focus();
        return false;
    }
    return true;
}

/**
* Create the mix
*/

function createMix(theForm) {
    // if (checkMixName(theForm.mix_name)) {
    if (checkNameValidity(theForm.mix_name.value)) {
        ajaxUpdateContainerWithStrutsAction('/vcctl/operation/prepareMix.do', theForm, 'content');
    }
// }
}

/**
* Hydration
*/

function onChangeThermalConditions(radioButton) {
    if (radioButton.value == "semi-adiabatic") {
        display("ambient_temperature");
        display("heat_transfer_coefficient");
    } else {
        hide("ambient_temperature");
        hide("heat_transfer_coefficient");
    }
}

function onChangeInitialTemperature(initialTemperatureField) {
    var theForm = initialTemperatureField.form;
    theForm.aggregate_initial_temperature.value = initialTemperatureField.value;
    theForm.ambient_temperature.value = initialTemperatureField.value;
    return true;
}

function onChangeOutputOption(radioButton) {
    theForm = radioButton.form;
    if (radioButton.value == "specify_times") {
        theForm.output_hydrating_microstructure_times.disabled=false;
        theForm.file_with_output_times.disabled=true;
    } else if (radioButton.value == "specify_file") {
        theForm.output_hydrating_microstructure_times.disabled=true;
        theForm.file_with_output_times.disabled=false;
    }
}

function onChangeDeactivationTime(field) {
    var value = field.value;
    if (isNaN(value) || value < 0) {
        field.value = 0.0;
        field.focus();
        alert("The deactivation time must be non-negative.");
        return false;
    } else {
        var propName = field.name;
        var modele = /.*\[([0-9]*)\].*/;
        var i = propName.replace(modele,"$1");

        var reactivationBeginningTimeField = field.form["surface_deactivation[" + i + "].reactivation_begin_time"];
        var reactivationBeginningValue = reactivationBeginningTimeField.value;
        if (value > reactivationBeginningValue) {
            field.value = reactivationBeginningValue;
            alert("Time for initial deactivation must be lower than or equal to the time for beginning reactivation");
            return false;
        }

        var fullReactivationTimeField = field.form["surface_deactivation[" + i + "].full_reactivation_time"];
        var fullReactivationTimeValue = fullReactivationTimeField.value;
        if (value > fullReactivationTimeValue) {
            field.value = fullReactivationTimeValue;
            alert("Time for initial deactivation must be lower than or equal to the time for terminating the reactivation");
            return false;
        }
    }
    return true;
}

function onChangeReactivationBeginTime(field) {
    var value = field.value;
    if (isNaN(value) || value < 0) {
        field.value = 0.0;
        field.focus();
        alert("The reactivation beginning time must be non-negative.");
        return false;
    } else {
        var propName = field.name;
        var modele = /.*\[([0-9]*)\].*/;
        var i = propName.replace(modele,"$1");

        var deactivationTimeField = field.form["surface_deactivation[" + i + "].deactivation_time"];
        var deactivationTimeValue = deactivationTimeField.value;
        if (value < deactivationTimeValue) {
            field.value = deactivationTimeValue;
            alert("Time for beginning reactivation must be greater than or equal to the time of initial deactivation");
            return false;
        }

        var fullReactivationTimeField = field.form["surface_deactivation[" + i + "].full_reactivation_time"];
        var fullReactivationTimeValue = fullReactivationTimeField.value;
        if (value > fullReactivationTimeValue) {
            field.value = fullReactivationTimeValue;
            alert("Time for beginning reactivation must be lower than or equal to the time for terminating the reactivation");
            return false;
        }
    }
    return true;
}

function onChangeFullReactivationTime(field) {
    var value = field.value;
    if (isNaN(value) || value < 0) {
        field.value = 0.0;
        field.focus();
        alert("The reactivation termination time must be non-negative.");
        return false;
    } else {
        var propName = field.name;
        var modele = /.*\[([0-9]*)\].*/;
        var i = propName.replace(modele,"$1");

        var deactivationTimeField = field.form["surface_deactivation[" + i + "].deactivation_time"];
        var deactivationTimeValue = deactivationTimeField.value;
        if (value < deactivationTimeValue) {
            field.value = deactivationTimeValue;
            alert("Time for terminating reactivation must be greater than or equal to the time of initial deactivation");
            return false;
        }

        var reactivationBeginningTimeField = field.form["surface_deactivation[" + i + "].reactivation_begin_time"];
        var reactivationBeginningValue = reactivationBeginningTimeField.value;
        if (value < reactivationBeginningValue) {
            field.value = reactivationBeginningValue;
            alert("Time for terminating reactivation must be greater than or equal to the time for beginning reactivation");
            return false;
        }
    }
    return true;
}

function onChangeCsh_seeds(field) {
    var value = field.value;
    if (isNaN(value) || value < 0) {
        field.value = 0.0;
        field.focus();
        alert("The number of CSH seeds must be in the range [0,1)");
        return false;
    } else if (value >= 1.0) {
        field.value = 0.5;
        field.focus();
        alert("The number of CSH seeds must be in the range [0,1)");
        return false;
    }
    return true;
}

var savedFramesNumber;

function createMovie(checkBox) {
    var theForm = checkBox.form;
    var enable = checkBox.checked;
    theForm.create_movie_frames.disabled = !enable;
    if (enable && savedFramesNumber != null && savedFramesNumber != 0) {
        theForm.create_movie_frames.value = savedFramesNumber;
    } else {
        savedFramesNumber = theForm.create_movie_frames.value;
        theForm.create_movie_frames.value = 0;
    }
}

function onChangeMovieFrames(field) {
    var theForm = field.form;
    if (field.value == 0) {
        theForm.create_movie.checked = false;
        field.disabled = true;
    }
}

function createHydration(theForm) {
    if (checkNameValidity(theForm.operation_name.value)) {
        ajaxUpdateContainerWithStrutsAction('/vcctl/operation/hydrateMix.do', theForm, 'content');
    }
}

function changeAgingMode(radioButton) {
    if (radioButton.value == "time") {
        $('aging-colorimetry_mode_parameters').hide();
        $('aging-chemical_shrinkage_mode_parameters').hide();
        $('aging-time_conversion_factor_mode_parameters').show();
    } else if (radioButton.value == "calorimetry") {
        $('aging-chemical_shrinkage_mode_parameters').hide();
        $('aging-time_conversion_factor_mode_parameters').hide();
        $('aging-colorimetry_mode_parameters').show();
    } else if (radioButton.value == "chemical_shrinkage") {
        $('aging-colorimetry_mode_parameters').hide();
        $('aging-time_conversion_factor_mode_parameters').hide();
        $('aging-chemical_shrinkage_mode_parameters').show();
    }
}

function changeCalorimetryFile(theForm) {
    theForm.request({
        parameters: {
            action:'check_calorimetry_file'
        },
        onComplete:  function(transport) {
            if (transport.responseText == "calFile_lessthan_24h") {
                alert("SEVERE: These calorimetry data cover less than 24 h.\nThere is a STRONG likelihood that the hydration kinetics will not extrapolate accurately to later ages.");
            } else if (transport.responseText == "calFile_lessthan_48h"){
                alert("WARNING: These calorimetry data cover less than 48 h.\nHydration kinetics may not extrapolate accurately to later ages.");
            }
        }
    })
}

/**
* My files functions
*/
function viewMicrostructureFile(file, linkID, classOfElementsToReload) {
    var url = "/vcctl/my-files/editMyMicrostructureFiles.do";
    var form = document.forms[0];
    if (!classOfElementsToReload) {
        classOfElementsToReload = "to-reload";
    }
    var fieldName = file + '.viewContent';
    if (form[fieldName].value.toLowerCase() == "true" || form[fieldName].value.toLowerCase() == "yes") {
        form[fieldName].value = false;
        $(linkID).innerHTML = "Show";
    } else {
        form[fieldName].value = true;
        $(linkID).innerHTML = "Hide";
    }
    ajaxUpdateElementsWithStrutsAction(url,form,classOfElementsToReload);
}

function viewAggregateFile(file, linkID, classOfElementsToReload) {
    var url = "/vcctl/my-files/editMyAggregateFiles.do";
    var form = document.forms[0];
    if (!classOfElementsToReload) {
        classOfElementsToReload = "to-reload";
    }
    var fieldName = file + '.viewContent';
    if (form[fieldName].value.toLowerCase() == "true" || form[fieldName].value.toLowerCase() == "yes") {
        form[fieldName].value = false;
        $(linkID).innerHTML = "Show";
    } else {
        form[fieldName].value = true;
        $(linkID).innerHTML = "Hide";
    }
    ajaxUpdateElementsWithStrutsAction(url,form,classOfElementsToReload);
}

function viewHydrationFile(file, linkID, classOfElementsToReload) {
    var url = "/vcctl/my-files/editMyHydrationFiles.do";
    var form = document.forms[0];
    if (!classOfElementsToReload) {
        classOfElementsToReload = "to-reload";
    }
    var fieldName = file + '.viewContent';
    if (form[fieldName].value.toLowerCase() == "true" || form[fieldName].value.toLowerCase() == "yes") {
        form[fieldName].value = false;
        $(linkID).innerHTML = "Show";
    } else {
        form[fieldName].value = true;
        $(linkID).innerHTML = "Hide";
    }
    ajaxUpdateElementsWithStrutsAction(url,form,classOfElementsToReload);
}

function viewMechanicalFile(file, linkID, classOfElementsToReload) {
    var url = "/vcctl/my-files/editMyMechanicalFiles.do";
    var form = document.forms[0];
    if (!classOfElementsToReload) {
        classOfElementsToReload = "to-reload";
    }
    var fieldName = file + '.viewContent';
    if (form[fieldName].value.toLowerCase() == "true" || form[fieldName].value.toLowerCase() == "yes") {
        form[fieldName].value = false;
        $(linkID).innerHTML = "Show";
    } else {
        form[fieldName].value = true;
        $(linkID).innerHTML = "Hide";
    }
    ajaxUpdateElementsWithStrutsAction(url,form,classOfElementsToReload);
}

function viewTransportFile(file, linkID, classOfElementsToReload) {
    var url = "/vcctl/my-files/editMyTransportFiles.do";
    var form = document.forms[0];
    if (!classOfElementsToReload) {
        classOfElementsToReload = "to-reload";
    }
    var fieldName = file + '.viewContent';
    if (form[fieldName].value.toLowerCase() == "true" || form[fieldName].value.toLowerCase() == "yes") {
        form[fieldName].value = false;
        $(linkID).innerHTML = "Show";
    } else {
        form[fieldName].value = true;
        $(linkID).innerHTML = "Hide";
    }
    ajaxUpdateElementsWithStrutsAction(url,form,classOfElementsToReload);
}

function saveMaterial(theForm, materialName, literalMaterialName) {
    theForm.request({
        parameters: {
            action:'save_' + materialName
        },
        onComplete:  function(transport) {
            if (transport.responseText == "problem_when_saving_" + materialName) {
                alert("A problem occurred. Your " + literalMaterialName + " has NOT been saved.");
            } else if (transport.responseText == "calFile_lessthan_24h") {
               alert("SEVERE: These calorimetry data cover less than 24 h.\nThere is a STRONG likelihood that the hydration kinetics will not extrapolate accurately to later ages.");
            } else if (transport.responseText == "calFile_lessthan_48h"){
                alert("WARNING: These calorimetry data cover less than 48 h.\nHydration kinetics may not extrapolate accurately to later ages.");
            }
            alert("Your " + literalMaterialName +" has been saved");
        }
    })
}

function saveAggregateAs(theForm, materialName, literalMaterialName) {
    var display_name = prompt("Save As:","")
    if (display_name) {
        if (display_name.length > 64 || display_name.length < 3) {
            alert("The " + literalMaterialName + " name must be between 3 and 64 characters.");
            return false;
        }

        if (!checkNameValidity(display_name)) {
            alert("The " + literalMaterialName + " name is not valid. Try to use another name, with no punctuation marks. Some names are reserved and can not be used, too.");
            return false;
        }

        classOfElementsToReload = materialName + "-element-to-reload";

        theForm.request({
            parameters: {
                'action':'save_' + materialName + '_as',
                'display_name':display_name
            },
            onComplete:  function(transport) {
                if (transport.responseText == materialName + "_name_alreadyTaken") {
                    alert("There already is a " + literalMaterialName + " with the same name.");
                    saveAggregateAs(theForm, literalMaterialName);
                } else if (transport.responseText == "problem_when_saving_" + materialName) {
                    alert("A problem occurred. Your " + literalMaterialName + " has NOT been saved.");
                } else {
                    alert("Your " + literalMaterialName + " has been saved");
                    // expandedElements = document.getElementsByClassName('expanded');
                    expandedElements = $$('.expanded');
                    //Split the text response into elements which the class is classOfElementsToReload
                    classElements = splitTextIntoElements(transport.responseText, classOfElementsToReload);

                    //Use these elements to update the page
                    replaceExistingWithNewHtml(classElements, classOfElementsToReload);
                    $('save_' + materialName).show();
                    $('delete_' + materialName).show();
                }
            }
        })
    }
    return false;
}

function saveMaterialAs(theForm, materialName, literalMaterialName) {
    var name = prompt("Save As:","")

    if (name) {
        if (name.length > 64 || name.length < 3) {
            alert("The " + literalMaterialName + " name must be between 3 and 64 characters.");
            return false;
        }

        if (!checkNameValidity(name)) {
            alert("The " + literalMaterialName + " name is not valid. Try to use another name, with no punctuation marks. Some names are reserved and can not be used, too.");
            return false;
        }

        classOfElementsToReload = materialName + "-element-to-reload";

        theForm.request({
            parameters: {
                'action':'save_' + materialName + '_as',
                'name': name
            },
            onComplete:  function(transport) {
                if (transport.responseText == materialName + "_name_alreadyTaken") {
                    alert("There already is a " + literalMaterialName + " with the same name.");
                    saveMaterialAs(theForm, literalMaterialName);
                } else if (transport.responseText == "problem_when_saving_" + materialName) {
                    alert("A problem occurred. Your " + literalMaterialName + " has NOT been saved.");
                } else {
                    alert("Your " + literalMaterialName + " has been saved");
                    // expandedElements = document.getElementsByClassName('expanded');
                    expandedElements = $$('.expanded');
                    //Split the text response into elements which the class is classOfElementsToReload
                    classElements = splitTextIntoElements(transport.responseText, classOfElementsToReload);

                    //Use these elements to update the page
                    replaceExistingWithNewHtml(classElements, classOfElementsToReload);
                    $('save_' + materialName).show();
                    $('delete_' + materialName).show();
                }
            }
        })
    }
    return false;
}

function deleteMaterial(theForm, materialName, literalMaterialName) {
    var confirmDelete = confirm('Are you sure you want to delete the ' + literalMaterialName + "?");
    if (confirmDelete) {
        theForm.request({
            parameters: {
                action:'delete_' + materialName
            },
            onComplete:  function(transport) {
                if (transport.responseText == "problem_when_deleting_" + materialName) {
                    alert("A problem occurred. Your " + literalMaterialName + " has NOT been deleted.");
                } else {
                    alert("Your " + literalMaterialName +" has been deleted.");
                }
            }
        })
    }
}

function onChangeCement(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "cement-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_cement').hide();
        //$('delete_cement').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=new_cement', form, classOfElementsToReload);
        $('save_cement').show();
        $('delete_cement').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=change_cement', form, classOfElementsToReload);
    } else {
        $('save_cement').show();
        $('delete_cement').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=change_cement', form, classOfElementsToReload);
    }
}

function saveCement(theForm) {
    saveMaterial(theForm, 'cement', 'cement');
}

function saveCementAs(theForm) {
    saveMaterialAs(theForm, 'cement', 'cement');
}

function deleteCement(theForm) {
    deleteMaterial(theForm, 'cement', 'cement');
}

function onChangeCoarseAggregate(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "coarse_aggregate-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_coarse_aggregate').hide();
        //$('delete_coarse_aggregate').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=new_coarse_aggregate', form, classOfElementsToReload);
        $('save_coarse_aggregate').show();
        $('delete_coarse_aggregate').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=change_coarse_aggregate', form, classOfElementsToReload);
    } else {
        $('save_coarse_aggregate').show();
        $('delete_coarse_aggregate').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=change_coarse_aggregate', form, classOfElementsToReload);
    }
}

function saveCoarseAggregate(theForm) {
    saveMaterial(theForm, 'coarse_aggregate', 'coarse_aggregate');
}

function saveCoarseAggregateAs(theForm) {
    saveAggregateAs(theForm, 'coarse_aggregate', 'coarse_aggregate');
}

function deleteCoarseAggregate(theForm) {
    deleteMaterial(theForm, 'coarse_aggregate', 'coarse_aggregate');
}

function onChangeFineAggregate(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "fine_aggregate-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_fine_aggregate').hide();
        //$('delete_fine_aggregate').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=new_fine_aggregate', form, classOfElementsToReload);
        $('save_fine_aggregate').show();
        $('delete_fine_aggregate').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=change_fine_aggregate', form, classOfElementsToReload);
    } else {
        $('save_fine_aggregate').show();
        $('delete_fine_aggregate').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editAggregateMaterials.do?action=change_fine_aggregate', form, classOfElementsToReload);
    }
}

function saveFineAggregate(theForm) {
    saveMaterial(theForm, 'fine_aggregate', 'fine_aggregate');
}

function saveFineAggregateAs(theForm) {
    saveAggregateAs(theForm, 'fine_aggregate', 'fine_aggregate');
}

function deleteFineAggregate(theForm) {
    deleteMaterial(theForm, 'fine_aggregate', 'fine_aggregate');
}

function startUploadCallback() {
    document.forms[0].action.value='upload';
    return true;
}

function completeUploadCallback(response) {
    // If response is a JSON string, that means that either an alkali or a PSD already has the same name as the one in the ZIP file in the database
    try {
        var data = response.evalJSON(true);
    } catch(e) {}
	
    if (data) {
        var url;
        if (data.existingFiles.length > 1) {
            // There already are a PSD AND an alkali with the same name
            var message = data.existingFiles[0].message;
            var type = data.existingFiles[0].type;
            var useExistingPSD = confirm(message + "\nDo you want to use the existing " + type + " or to create a new one?\n\nClick OK to use the existing one or Cancel to create a new one.");
			
            var psdName = "";
            if (!useExistingPSD) {
                psdName = prompt('Enter the name of the ' + type + ':', data.existingFiles[0].newName);
                if (psdName == null || psdName == "") {
                    useExistingPSD = true;
                    psdName = ""; // if we don't assign an empty string to psdName, the String "null" will be passed
                }
            }
			
            message = data.existingFiles[1].message;
            type = data.existingFiles[1].type;
            var useExistingAlkali = confirm(message + "\nDo you want to use the existing " + type + " or to create a new one?\n\nClick OK to use the existing one or Cancel to create a new one.");
			
            var alkaliName = "";
            if (!useExistingAlkali) {
                alkaliName = prompt('Enter the name of the alkali' + type + ':', data.existingFiles[1].newName);
                if (alkaliName == null || alkaliName == "") {
                    useExistingAlkali = true;
                    alkaliName = ""; // if we don't assign an empty string to alkaliName, the String "null" will be passed
                }
            }
			
            if (useExistingPSD && useExistingAlkali) {
                url = '/vcctl/lab-materials/editCementMaterials.do?action=use_existing_psd_or_alkali';
            } else {
                url = '/vcctl/lab-materials/editCementMaterials.do?action=create_new_psd_or_alkali&psdName=' + psdName + '&alkaliName=' + alkaliName;
            }
        } else {
            message = data.existingFiles[0].message;
            type = data.existingFiles[0].type;
            var useExisting = confirm(message + "\nDo you want to use the existing " + type + " or to create a new one?\n\nClick OK to use the existing one or Cancel to create a new one.");
			
            var name = "";
            if (!useExisting) {
                name = prompt('Enter the name the ' + type + ':', data.existingFiles[0].newName);
                if (name == null || name == "") {
                    useExisting = true;
                    name = ""; // if we don't assign an empty string to name, the String "null" will be passed
                }
            }
			
            psdName = "";
            alkaliName = "";
            if (type == "psd") {
                psdName = name;
            } else {
                alkaliName = name;
            }
			
            if (useExisting) {
                url = '/vcctl/lab-materials/editCementMaterials.do?action=use_existing_psd_or_alkali';
            } else {
                url = '/vcctl/lab-materials/editCementMaterials.do?action=create_new_psd_or_alkali&psdName=' + psdName + '&alkaliName=' + alkaliName;
            }
        }
        new Ajax.Request(url, {
            method: 'post',
            evalScripts:true,
            onSuccess: function(transport) {
                completeUploadCallback(transport.responseText);
            }
        });
        return;
    }
    // Since the input file isn't correctly reintialized with some brothers, let's remove it.
    // It will be re-added later by the replaceExistingWithNewHtml function.
    $('cement_zip_file_input').remove();

    classOfElementsToReload = "cement-element-to-reload";
    classElements = splitTextIntoElements(response, classOfElementsToReload);
    replaceExistingWithNewHtml(classElements, classOfElementsToReload);
}

function onChangeSlag(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "slag-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_slag').hide();
        //$('delete_slag').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=new_slag', form, classOfElementsToReload);
        $('save_slag').show();
        $('delete_slag').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=change_slag', form, classOfElementsToReload);
    } else {
        $('save_slag').show();
        $('delete_slag').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editSlagMaterials.do?action=change_slag', form, classOfElementsToReload);
    }
}

function saveSlag(theForm) {
    saveMaterial(theForm, 'slag', 'slag');
}

function saveSlagAs(theForm) {
    saveMaterialAs(theForm, 'slag', 'slag');
}

function deleteSlag(theForm) {
    deleteMaterial(theForm, 'slag', 'slag');
}

function onChangeFlyAsh(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "fly_ash-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_fly_ash').hide();
        //$('delete_fly_ash').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=new_fly_ash', form, classOfElementsToReload);
        $('save_fly_ash').show();
        $('delete_fly_ash').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=change_fly_ash', form, classOfElementsToReload);
    } else {
        $('save_fly_ash').show();
        $('delete_fly_ash').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFlyAshMaterials.do?action=change_fly_ash', form, classOfElementsToReload);
    }
}

function saveFlyAsh(theForm) {
    saveMaterial(theForm, 'fly_ash', 'fly ash');
}

function saveFlyAshAs(theForm) {
    saveMaterialAs(theForm, 'fly_ash', 'fly ash');
}

function deleteFlyAsh(theForm) {
    deleteMaterial(theForm, 'fly_ash', 'fly ash');
}

function onChangeInertFiller(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "inert_filler-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_inert_filler').hide();
        //$('delete_inert_filler').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFillerMaterials.do?action=new_inert_filler', form, classOfElementsToReload);
        $('save_inert_filler').show();
        $('delete_inert_filler').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFillerMaterials.do?action=change_inert_filler', form, classOfElementsToReload);
    } else {
        $('save_inert_filler').show();
        $('delete_inert_filler').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editFillerMaterials.do?action=change_inert_filler', form, classOfElementsToReload);
    }
}

function saveInertFiller(theForm) {
    saveMaterial(theForm, 'inert_filler', 'inert filler');
}

function saveInertFillerAs(theForm) {
    saveMaterialAs(theForm, 'inert_filler', 'inert filler');
}

function deleteInertFiller(theForm) {
    deleteMaterial(theForm, 'inert_filler', 'inert filler');
}

function onChangeCementDataFile(popupMenu) {
    var form = popupMenu.form;

    classOfElementsToReload = "cement_data_file-element-to-reload";

    if (popupMenu.selectedIndex == 0) { // If the user selected "New _materialName_..."
        //$('save_cement_data_file').hide();
        //$('delete_cement_data_file').hide();
        //ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=new_cement_data_file', form, classOfElementsToReload);
        $('save_cement_data_file').show();
        $('delete_cement_data_file').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=change_cement_data_file', form, classOfElementsToReload);
    } else {
        $('save_cement_data_file').show();
        $('delete_cement_data_file').show();
        ajaxUpdateElementsWithStrutsAction('/vcctl/lab-materials/editCementMaterials.do?action=change_cement_data_file', form, classOfElementsToReload);
    }
}

function saveCementDataFile(theForm) {
    saveMaterial(theForm, 'cement_data_file', 'cement data file');
}

function saveCementDataFileAs(theForm) {
    saveMaterialAs(theForm, 'cement_data_file', 'cement data file');
}

function deleteDataFile(theForm) {
    deleteMaterial(theForm, 'cement_data_file', 'cement data file');
}

function startUploadCoarseAggregateCallback() {
    document.forms[0].action.value='upload_coarse_aggregate';
    return true;
}

function completeUploadCoarseAggregateCallback(response) {
    try {
        var data = response.evalJSON(true);
    } catch(e) {}

    if (data) {
        var url;
        if (data.noShapeFiles.length > 1) {
            var message = data.existingFiles[0].message;
            alert(message);
        }
    }
    // Since the input file isn't correctly reintialized with some brothers, let's remove it.
    // It will be re-added later by the replaceExistingWithNewHtml function.
    $('coarse_aggregate_zip_file_input').remove();

    classOfElementsToReload = "coarse_aggregate-element-to-reload";
    classElements = splitTextIntoElements(response, classOfElementsToReload);
    replaceExistingWithNewHtml(classElements, classOfElementsToReload);
}

function startUploadFineAggregateCallback() {
    document.forms[0].action.value='upload_fine_aggregate';
    return true;
}

function completeUploadFineAggregateCallback(response) {
    try {
        var data = response.evalJSON(true);
    } catch(e) {}

    if (data) {
        var url;
        if (data.noShapeFiles.length > 1) {
            var message = data.existingFiles[0].message;
            alert(message);
        }
    }
    // Since the input file isn't correctly reintialized with some brothers, let's remove it.
    // It will be re-added later by the replaceExistingWithNewHtml function.
    $('fine_aggregate_zip_file_input').remove();

    classOfElementsToReload = "fine_aggregate-element-to-reload";
    classElements = splitTextIntoElements(response, classOfElementsToReload);
    replaceExistingWithNewHtml(classElements, classOfElementsToReload);
}

/**
* Common functions
*/

function hideOrDisplay(divID) {
    var element = $(divID);
    if (element.hasClassName("hidden")) {
        element.removeClassName("hidden");
    }
    else {
        element.addClassName("hidden");
    }
}

function hide(divID) {
    var element = $(divID);
    if (element && !element.hasClassName("hidden")) {
        element.addClassName("hidden");
    }
}

function display(divID) {
    var element = $(divID);
    if (element && element.hasClassName("hidden")) {
        element.removeClassName("hidden");
    }
}

function collapseExpand(divID)
{
    var element = $(divID);
    if (element.hasClassName("collapsed")) {
        element.removeClassName("collapsed");
        element.addClassName("expanded");
    }
    else if (element.hasClassName("expanded")) {
        element.removeClassName("expanded");
        element.addClassName("collapsed");
    }

    // element = $(divID).getElementsByClassName('collapsable-content')[0];
    element = $(divID).select('.collapsable-content')[0];
    if (element.hasClassName("collapsed")) {
        element.removeClassName("collapsed");
        element.addClassName("expanded");
    }
    else if (element.hasClassName("expanded")) {
        element.removeClassName("expanded");
        element.addClassName("collapsed");
    }
    // element = $(divID).getElementsByClassName('collapsable-title')[0];
    element = $(divID).select('.collapsable-title')[0];
    if (element.hasClassName("collapsed")) {
        element.removeClassName("collapsed");
        element.addClassName("expanded");
    }
    else if (element.hasClassName("expanded")) {
        element.removeClassName("expanded");
        element.addClassName("collapsed");
    }
}

/**
* Check if the value of the field is >=min and <=max
* @param field the field to be checked
* @param name the name of the field so that the right alert message is displayed in case of the value isn't correct
* @param min (optional) the minimum value. If not given, minimum value = 0.
* @param max (optional) the maximum value. If not given, maximum value = 1.
**/
function checkFieldValue(field, name, min, max) {
    if (min == undefined) {
        min = 0.0;
    }
    if (max == undefined) {
        max = 1.0;
    }
    var result = checkValue(parseFloat(field.value),name,min,max);
    if (result == false) {
        field.value=min;
        field.focus();
    }
    return result;
}

/**
* Check if the value is >=min and <=max
* @param value the value to be checked
* @param name the name of the field so that the right alert message is displayed in case of the value isn't correct
* @param min (optional) the minimum value. If not given, minimum value = 0.
* @param max (optional) the maximum value. If not given, maximum value = 1.
**/
function checkValue(value, name, min, max) {
    if (min == undefined) {
        min = 0.0;
    }
    if (max == undefined) {
        max = 1.0;
    }
    if((value<min) || (value>max) || (isNaN(value))) {
        var alertMsg = name + " must be in the range ["+ min + "," + max + "]";
        alert(alertMsg);
        return false;
    }
    return true;
}

/**
* Check if the value of the field is >=min and <=max and return the value
* @param field the field to be checked
* @param name the name of the field so that the right alert message is displayed in case of the value isn't correct
* @param min (optional) the minimum value. If not given, minimum value = 0.
* @param max (optional) the maximum value. If not given, maximum value = 1.
**/
function checkAndGetValueOfField(field, name, min, max) {
    if (min == undefined) {
        min = 0.0;
    }
    if (max == undefined) {
        max = 1.0;
    }
    var value = parseFloat(field.value);
    if (checkValue(value,name,min,max) == false) {
        field.value=min;
        field.focus();
        return min;
    }
    return value;
}

var sliders = new Array();

function createSliderAssociatedWithField(theField, min, max, increment, initialValue) {
    var handleName = theField.name + '-handle';
    var trackName = theField.name + '-track';
    var slider = new Control.Slider(handleName,trackName,{
        minimum:min,
        maximum:max,
        increment:increment,
        sliderValue:initialValue,
        onSlide:function(v){
            theField.value = v.toNiceFixed(2);
        }
    }
    );
    var sliderName = theField.name + 'Slider';
    sliders[sliderName] = slider;
}

function onChangeSliderValue(theField) {
    var handleName = theField.name + '-handle';
    var sliderName = theField.name + 'Slider';
    var min = sliders[sliderName].minimum;
    var max = sliders[sliderName].maximum;
    var newValue = checkAndGetValueOfField(theField,'The hydration degree',min,max);
    sliders[sliderName].setValue(theField.value);
}

var newwindow;

function openInNewWindow(url) {
    newwindow = window.open(url,'','menubar=no,height=800,width=1056,resizable=yes,toolbar=no,location=no,status=no');
    if (window.focus) {
        newwindow.focus()
    }
}

/**
* Equivalent to toFixed() but removes all unecessary 0 after the decimal separator
* For browsers that don't support toFixed, it returns the string representation of the number
**/
Number.prototype.toNiceFixed = function(rounding) {
    if (this.toFixed) {
        return (Math.round(this*Math.pow(10,rounding))/Math.pow(10,rounding)).toString();
    }
    return (Math.round(this*Math.pow(10,rounding))/Math.pow(10,rounding)).toString();
}

function trim(s) {
    if ((s==null) || (typeof(s) != 'string') || !s.length) {
        return'';
    }
    return s.replace(/^\s+/,'').replace(/\s+$/,'');
}
