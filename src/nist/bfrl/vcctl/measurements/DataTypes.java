/*
 * DataTypes.java
 *
 * Created on July 21, 2007, 11:11 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

import java.util.*;
import nist.bfrl.vcctl.util.Util;

/**
 *
 * @author mscialom
 */
public class DataTypes {
    
    /**
     * Hydration data types
     **/

    private static HashMap hydrationDataTypes;
    
    public static HashMap<String,String> getHydrationDataTypes() {
        return hydrationDataTypes;
    }
    
    public static String nameOf(String displayName) {
        if (displayName != null && displayName.length() > 0 && hydrationDataNames.length == hydrationDataDisplayNames.length) {
            return hydrationDataNames[Util.searchStringInArray(displayName,hydrationDataDisplayNames)];
        }
        return null;
    }

    public static String legendNameOf(String displayName) {
        if (displayName != null && displayName.length() > 0 && hydrationDataLegendNames.length == hydrationDataDisplayNames.length) {
            return hydrationDataLegendNames[Util.searchStringInArray(displayName,hydrationDataDisplayNames)];
        }
        return null;
    }
    
    public static String displayNameOf(String name) {
        if (name != null && name.length() > 0 && hydrationDataNames.length == hydrationDataDisplayNames.length) {
            return hydrationDataDisplayNames[Util.searchStringInArray(name,hydrationDataNames)];
        }
        return null;
    }
    
    public static String fullDisplayNameOf(String name) {
        String unit = unitOf(name);
        if (name != null && name.length() > 0 && unit != null && unit.length() > 0 && !unit.equalsIgnoreCase("no unit"))
            return displayNameOf(name) + " (" + unit + ")";
        return displayNameOf(name);
    }
    
    public static String unitOf(String name) {
        if (name != null && name.length() > 0 && hydrationDataNames.length == hydrationDataUnits.length) {
            return hydrationDataUnits[Util.searchStringInArray(name,hydrationDataNames)];
        }
        return null;
    }
    
    public static String unitOfDisplayName(String displayName) {
        if (displayName != null && displayName.length() > 0 && hydrationDataNames.length == hydrationDataUnits.length) {
            return hydrationDataUnits[Util.searchStringInArray(displayName,hydrationDataDisplayNames)];
        }
        return null;
    }
    
    public static String symbolOf(String name) {
        if (name != null && name.length() > 0 && hydrationDataNames.length == hydrationDataSymbols.length) {
            return hydrationDataSymbols[Util.searchStringInArray(name,hydrationDataNames)];
        }
        return null;
    }
    
    static String[] hydrationDataNames = {"Cycle", "time(h)", "Alpha_mass", "Alpha_fa_mass", "heat(kJ/kg_solid)",
    "Temperature(C)", "Gsratio", "Wno(g/g)", "Wni(g/g)", "ChemShrink(mL/g)", "pH", "Conductivity(S/m)",
    "[Na+](M)", "[K+](M)", "[Ca++](M)", "[SO4--](M)", "{K+}", "{Ca++}", "{OH-}", "{SO4--}", "Vfpore",
    "Poreconnx", "Poreconny", "Poreconnz", "Poreconnave", "Solidconnx", "Solidconny", "Solidconnz",
    "Solidconnave", "VfC3S", "VfC2S", "VfC3A", "VfOC3A", "VfC4AF", "VfK2SO4", "VfNA2SO4", "VfGYPSUM",
    "VfHEMIHYD", "VfANHYDRITE", "VfCACO3", "VfFREELIME", "VfSFUME", "VfINERT", "VfSLAG", "VfASG",
    "VfCAS2", "VfAMSIL", "VfCH", "VfCSH", "VfPOZZCSH", "VfSLAGCSH", "VfC3AH6", "VfETTR", "VfAFM",
    "VfFH3", "VfCACL2", "VfFRIEDEL", "VfSTRAT", "VfGYPSUMS", "VfABSGYP", "VfAFMC", "VfINERTAGG",
    "VfEMPTYP"};
    
    static String[] hydrationDataDisplayNames = {"Cycles", "Time", "Degree of Hydration of cement",
    "Degree of Hydration of fly ash", "Heat release", "Temperature of binder", "Gel-space ratio",
    "Non-evaporable water (unignited)", "Non-evaporable water (ignited)", "Chemical shrinkage", "Solution pH",
    "Solution conductivity", "Concentration of sodium in solution", "Concentration of potassium in solution",
    "Concentration of calcium in solution", "Concentration of sulfate in solution",
    "Activity of potassium in solution", "Activity of calcium in solution", "Activity of hydroxyl in solution",
    "Activity of sulfate in solution", "Total porosity", "Fraction porosity connected x direction",
    "Fraction porosity connected y direction", "Fraction porosity connected z direction",
    "Average fraction porosity connected", "Fraction solids connected x direction",
    "Fraction solids connected y direction", "Fraction solids connected z direction",
    "Average fraction solids connected", "Volume fraction of C3S", "Volume fraction of C2S",
    "Volume fraction of C3A", "Volume fraction of OC3A", "Volume fraction of C4AF", "Volume fraction of K2SO4",
    "Volume fraction of Na2SO4", "Volume fraction of Gypsum", "Volume fraction of Hemihydrate",
    "Volume fraction of Anhydrite", "Volume fraction of CaCO3", "Volume fraction of CaO",
    "Volume fraction of Silica fume", "Volume fraction of Inert", "Volume fraction of Slag",
    "Volume fraction of AS glass", "Volume fraction of CAS2", "Volume fraction of Amorphous Silica",
    "Volume fraction of CH", "Volume fraction of CSH", "Volume fraction of Pozzolanic CSH",
    "Volume fraction of Slag CSH", "Volume fraction of C3AH6", "Volume fraction of Ettringite",
    "Volume fraction of Monosulfate", "Volume fraction of FH3", "Volume fraction of CaCl2",
    "Volume fraction of Friedel Salt", "Volume fraction of Stratlingite", "Volume fraction of Secondary Gypsum",
    "Volume fraction of Absorbed Gypsum", "Volume fraction of Carboaluminate", "Volume fraction of Aggregate",
    "Volume fraction of Empty Porosity"};

    static String[] hydrationDataLegendNames = {"Cycles", "Time", "DOH",
    "DOH Fly Ash", "Heat release", "Temperature", "Gel-space ratio",
    "Wn (unignited)", "Wn (ignited)", "Chemical shrinkage", "pH",
    "Conductivity", "[Na]", "[K]",
    "[Ca]", "[SO3]",
    "{K}", "{Ca}", "{OH}",
    "{SO3}", "Porosity", "Connected porosity:x",
    "Connected porosity:y", "Connected porosity:z",
    "<Connected porosity>", "Connected solids:x",
    "Connected solids:y", "Connected solids:z",
    "<Connected solids>", "VF(C3S)", "VF(C2S)",
    "VF(C3A)", "VF(OC3A)", "VF(C4AF)", "VF(K2SO4)",
    "VF(Na2SO4)", "VF(Gypsum)", "VF(Hemihydrate)",
    "VF(Anhydrite)", "VF(CaCO3)", "VF(CaO)",
    "VF(Silica fume)", "VF(Inert)", "VF(Slag)",
    "VF(AS glass)", "VF(CAS2)", "VF(Silica)",
    "VF(CH)", "VF(CSH)", "VF(Pozzolanic CSH)",
    "VF(Slag CSH)", "VF(C3AH6)", "VF(Ettringite)",
    "VF(Monosulfate)", "VF(FH3)", "VF(CaCl2)",
    "VF(Friedel Salt)", "VF(Stratlingite)", "VF(Secondary Gyp)",
    "VF(Absorbed Gyp)", "VF(Carboaluminate)", "VF(Aggregate)",
    "VF(Empty Porosity)"};

    static String[] hydrationDataUnits = {"no unit", "h", "no unit", "no unit", "kJ/kg solid", "°C", "no unit",
    "g/g cement", "g/g cement", "mL/g cement", "no unit", "Siemens/m", "mol/L", "mol/L",
    "mol/L", "mol/L", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit",
    "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit",
    "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit",
    "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit",
    "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit", "no unit"};
    
    static String[] hydrationDataSymbols = {"n", "t", "&alpha;", "&alpha; fa", "dQ/dt", "T", "X", "Wno", "Wni", "CHS", "pH",
    "Greek sigma", "[Na+]", "[K+]", "[Ca++]", "[SO4--]", "{K+}", "{Ca++}", "{OH-}", "{SO4--}", "&phi;_p",
    "&phi;_p, x^conn/phi_p", "&phi;_p, y^conn/phi_p", "&phi;_p, z^conn/phi_p", "&phi;_p, conn/phi_p",
    "&phi;_s, x^conn/phi_s", "&phi;_s, y^conn/phi_s", "&phi;_s, z^conn/phi_s", "&phi;_s^conn/phi_s", "f(C3S)",
    "f(C2S)", "f(C3A)", "f(OC3A)", "f(C4AF)", "f(K2SO4)", "f(Na2SO4)", "f(Gypsum)", "f(Hemihydrate)",
    "f(Anhydrite)", "f(CaCO3)", "f(CaO)", "f(SF)", "f(Inert)", "f(Slag)", "f(AS glass)", "f(CAS2 glass)",
    "f(Am. Silica)", "f(CH)", "f(CSH)", "f(Pozz. CSH)", "f(Slag CSH)", "f(C3AH6)", "f(Ettringite)",
    "f(Monosulfate)", "f(FH3)", "f(CaCl2)", "f(Friedel Salt)", "f(Stratlingite)", "f(Secondary Gypsum)",
    "f(Absorbed Gypsum)", "f(Carboaluminate)", "f(Aggregate)", "f(Empty Porosity)"};
    
    
}
