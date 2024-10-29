/*
 * FileTypes.java
 *
 * Created on November 25, 2005, 11:03 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.util;

import java.io.File;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.Map.Entry;

/**
 *
 * @author tahall
 */
public class FileTypes {
    
    static private String[] descr = 
    {
        "Input to genmic",
        "Output from genmic",
        "Microstructure image",
        "Particle SH coefficients",
        "One-pixel bias numbers",
        "Cement phase statistics",
        "K2O correlation kernel",
        "C4F correlation kernel",
        "Silicates correlation kernel",
        "C3S correlation kernel",
        "N2O correlation kernel",
        "Input to disrealnew",
        "Output from disrealnew",
        "Grading",
        "Input to genaggpack",
        "Output from genaggpack",
        "Cement alkali characteristics",
        "Fly ash alkali characteristics",
        "Slag characteristics",
        "Hydration results",
        "Hydration image",
        "Hydration movie",
        "C3A correlation kernel", // verify it's correct
        "Parameters file",
        "Aluminates correlation kernel",
        "Particle size distribution",
        "Particle image file",
        "Input to elastic",
        "Output from elastic",
        "Effective moduli results",
        "Phase contributions",
        "ITZ elastic characteristics",
        "Major transport output data",
        "Transport factor results",
        "Input to transport",
        "Output from transport",
        "Plain text file",
        "Pore size distribution"
    };
    
    private static int getType(String opname, String filename) {
        File f = new File(filename);
        String name = f.getName().toLowerCase();
        
        if (name.endsWith(".img.in")) { return 0; }
        else if (name.endsWith(".img.out")) { return 1; }
        else if (name.endsWith(".img")) { return 2; }
        else if (name.endsWith(".img.struct")) { return 3; }
        else if (name.endsWith(".bias")) { return 4; }
        else if (name.endsWith(".stt")) { return 5; }
        else if (name.endsWith(".k2o")) { return 6; }
        else if (name.endsWith(".c4f")) { return 7; }
        else if (name.endsWith(".sil")) { return 8; }
        else if (name.endsWith(".c3s")) { return 9; }
        else if (name.endsWith(".n2o")) { return 10; }
        else if (name.endsWith(".hyd.in")) { return 11; }
        else if (name.endsWith(".hyd.out")) { return 12; }
        else if (name.endsWith(".gdg")) { return 13; }
        else if (name.equalsIgnoreCase(Constants.GENAGGPACK_INPUT_FILE)) { return 14; }
        else if (name.equalsIgnoreCase(Constants.GENAGGPACK_OUTPUT_FILE)) { return 15; }
        else if (name.equalsIgnoreCase(Constants.CEMENT_ALKALI_CHARACTERISTICS_FILE)) { return 16; }
        else if (name.equalsIgnoreCase(Constants.FLY_ASH_ALKALI_CHARACTERISTICS_FILE)) { return 17; }
        else if (name.equalsIgnoreCase(Constants.SLAG_CHARACTERISTICS_FILE)) { return 18; }
        else if (name.endsWith(".data")) { return 19; }        
        else if (name.endsWith(".mov")) { return 21; }
        else if (name.indexOf(".c3a") > 0) { return 22; }
        else if (name.indexOf(".prm") > 0) { return 23; }
        else if (name.endsWith(".alu")) { return 24; }
        else if (name.endsWith(".psd")) { return 25; }
        else if (name.endsWith(".pimg")) { return 26; }
        else if (name.equalsIgnoreCase(Constants.ELASTIC_INPUT_FILE)) { return 27; }
        else if (name.equalsIgnoreCase(Constants.ELASTIC_OUTPUT_FILE)) { return 28; }
        else if (name.equalsIgnoreCase(Constants.EFFECTIVE_MODULI_FILE_NAME)) { return 29; }
        else if (name.equalsIgnoreCase(Constants.PHASE_CONTRIBUTIONS_FILE_NAME)) { return 30; }
        else if (name.equalsIgnoreCase(Constants.ITZ_MODULI_FILE_NAME)) { return 31; }
        else if (name.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_MAJOROUTPUT_FILE_NAME)) { return 32; }
        else if (name.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_RESULTS_FILE_NAME)) { return 33; }
        else if (name.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_INPUT_FILE)) { return 34; }
        else if (name.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_OUTPUT_FILE)) { return 35; }
        else if (name.endsWith(".txt")) { return 36; }
        else if (name.endsWith(".poredist")) { return 37; }
        else if (name.indexOf(".img") > 0) { return 20; }
        else { return -1; }
    }
    
    // Return the description of the file
    public static String description(String opname, String filename) {
        int ftype = getType(opname, filename);
        if (ftype >= 0) {
            return descr[ftype];
        } else {
            return "";
        }
    }
    
    
    static private HashMap<String,String> typeDescriptions = new HashMap();
    
    static {
        typeDescriptions.put(Constants.ALKALI_CHARACTERISTICS_TYPE, "Alkali characteristics");
        typeDescriptions.put(Constants.PSD_TYPE, "PSD");
        typeDescriptions.put(Constants.SLAG_CHARACTERISTICS_TYPE, "Slag characteristics");
        typeDescriptions.put(Constants.PARAMETER_FILE_TYPE, "Parameters file");
        typeDescriptions.put(Constants.CHEMICAL_SHRINKAGE_FILE_TYPE, "Chemical shrinkage file");
        typeDescriptions.put(Constants.CALORIMETRY_FILE_TYPE, "Calorimetry file");
        typeDescriptions.put(Constants.TIMING_OUTPUT_FILE_TYPE, "Timing output file");
    }
    
    public static String typeDescription(String type) {
        String description = typeDescriptions.get(type);
        if (description != null)
            return description;
        return "";
    }
    
    public static HashMap<String,String> getTypeDescriptions() {
        return typeDescriptions;
    }

    
    static private ArrayList<String> typeDescriptionList = new ArrayList();

    static {
        typeDescriptionList.add(Constants.ALKALI_CHARACTERISTICS_TYPE);
        typeDescriptionList.add(Constants.PSD_TYPE);
        typeDescriptionList.add(Constants.SLAG_CHARACTERISTICS_TYPE);
        typeDescriptionList.add(Constants.PARAMETER_FILE_TYPE);
        typeDescriptionList.add(Constants.CHEMICAL_SHRINKAGE_FILE_TYPE);
        typeDescriptionList.add(Constants.CALORIMETRY_FILE_TYPE);
        typeDescriptionList.add(Constants.TIMING_OUTPUT_FILE_TYPE);
    }


    public static ArrayList<String> getTypeDescriptionList() {
        return typeDescriptionList;
    }
    

    /*
    public static String typeCorrespondingToDescription(String description) {
        Iterator<Entry<String, String>> it = typeDescriptions.entrySet().iterator();
        while (it.hasNext()) {
            Entry<String, String> entry = it.next();
            if (entry.getValue().equalsIgnoreCase(description))
                return entry.getKey();
        }
        return "";
    }
     * */
    
    static private HashMap<String,String> cementFileExtensions = new HashMap();
    
    static {
        cementFileExtensions.put(".psd",Constants.PSD_TYPE);
        cementFileExtensions.put(".pfc","pfc");
        cementFileExtensions.put(".psv","psv");
        cementFileExtensions.put(".gif","gif");
        cementFileExtensions.put("_legend.gif","legend_gif");
        cementFileExtensions.put(".sil","sil");
        cementFileExtensions.put(".c3a","c3a");
        cementFileExtensions.put(".c3s","c3s");
        cementFileExtensions.put(".c4f","c4f");
        cementFileExtensions.put(".k2o","k2o");
        cementFileExtensions.put(".n2o","n2o");
        cementFileExtensions.put(".alu","alu");
        cementFileExtensions.put(".txt","txt");
        cementFileExtensions.put(".xrd","xrd");
        cementFileExtensions.put(".inf","inf");
        cementFileExtensions.put("_info.dat","inf");
        cementFileExtensions.put(".gyp","dihyd");
        cementFileExtensions.put(".hem","hemihyd");
        cementFileExtensions.put(".anh","anhyd");
        cementFileExtensions.put(".alk",Constants.ALKALI_CHARACTERISTICS_TYPE);
        cementFileExtensions.put(".zip","zip");
    }

    static private HashMap<String,String> aggregateFileExtensions = new HashMap();

    static {
        aggregateFileExtensions.put(".gif","gif");
        aggregateFileExtensions.put(".bmv","bulk_modulus");
        aggregateFileExtensions.put(".smv","shear_modulus");
        aggregateFileExtensions.put(".cnd","conductivity");
        aggregateFileExtensions.put(".sgv","specific_gravity");
        aggregateFileExtensions.put(".inf","inf");
        aggregateFileExtensions.put(".sst","shape_stats");
        aggregateFileExtensions.put(".zip","zip");
    }

    public static String getCementColumnNameCorrespondingToFileName(String fileName) {
        /*
        Iterator<String> it = cementFileExtensions.keySet().iterator();
        while(it.hasNext()) {
            String extension = it.next();
            if (fileName.endsWith(extension))
                return cementFileExtensions.get(extension);
        }
         */
        
        int dotIndex = fileName.lastIndexOf('.');
        String extension = fileName.substring(dotIndex);
        return FileTypes.cementFileExtensions.get(extension);
    }
    
    public static String getExtensionCorrespondingToType(String type) {
        Iterator<Entry<String, String>> it = FileTypes.cementFileExtensions.entrySet().iterator();
        String extension = null;
        while (it.hasNext()) {
            Entry<String, String> entry = it.next();
            if (entry.getValue().equalsIgnoreCase(type))
                return entry.getKey();
        }
        return extension;
    }
    
    public static boolean isValidCementFileName(String fileName) {
        if (!fileName.startsWith(".") && getCementColumnNameCorrespondingToFileName(fileName) != null)
            return true;
        return false;
    }

    public static String getAggregateColumnNameCorrespondingToFileName(String fileName) {
        /*
        Iterator<String> it = cementFileExtensions.keySet().iterator();
        while(it.hasNext()) {
            String extension = it.next();
            if (fileName.endsWith(extension))
                return cementFileExtensions.get(extension);
        }
         */

        int dotIndex = fileName.lastIndexOf('.');
        System.out.println("Aggregate column name dotIndex = " + dotIndex);
        String extension = fileName.substring(dotIndex);
        System.out.println("Aggregate extension = " + extension);
        System.out.println("From hashmap extension = " + FileTypes.aggregateFileExtensions.get(extension));
        return FileTypes.aggregateFileExtensions.get(extension);
    }

    public static String getAggregateExtensionCorrespondingToType(String type) {
        Iterator<Entry<String, String>> it = FileTypes.aggregateFileExtensions.entrySet().iterator();
        String extension = null;
        while (it.hasNext()) {
            Entry<String, String> entry = it.next();
            if (entry.getValue().equalsIgnoreCase(type))
                return entry.getKey();
        }
        return extension;
    }

    public static boolean isValidAggregateFileName(String fileName) {
        if (!fileName.startsWith(".") && getAggregateColumnNameCorrespondingToFileName(fileName) != null)
            return true;
        return false;
    }
}
