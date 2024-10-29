/*
 * Phase.java
 *
 * Created on May 31, 2005, 2:18 PM
 */

package nist.bfrl.vcctl.operation.microstructure;

import java.util.*;


/**
 *
 * @author tahall
 */
public class Phase {
    /*******************************
     **  Public static functions  **
     **                           **
     ******************************/
    
    /*
     * Return the phase number given the phase name or the associated
     * property name
     */
    static public int number(String nameorprop) {
        int index_match=-1;
        for (int i=0; i<phase_number.length; i++) {
            if (nameorprop.equalsIgnoreCase(phase_name[i])) {
                index_match = i;
                break;
            } else if (nameorprop.equalsIgnoreCase(phase_property_name[i])) {
                index_match = i;
                break;
            }
        }
        
        if (index_match == -1) {
            return -1;
        } else {
            return phase_number[index_match];
        }
    }
    
    static public int[] numbers() {
        int ns[] = new int[phase_number.length];
        for (int i=0; i<phase_number.length; i++) {
            ns[i] = phase_number[i];
        }
        
        return ns;
    }

    /*
     * Return the phase name given the phase number
     */
    static public String name(int number) {
        for (int i=0; i<phase_number.length; i++) {
            if (phase_number[i] == number) {
                return phase_name[i];
            }
        }
        return null;
    }

    static public String[] names() {
        String ns[] = new String[phase_name.length];
        for (int i=0; i<phase_name.length; i++) {
            ns[i] = phase_name[i];
        }
        
        return ns;
    }

    /*
     * Return the phase name given the property name
     */
    static public String name(String property) {
         for (int i=0; i<phase_property_name.length; i++) {
            if (phase_property_name[i].equalsIgnoreCase(property)) {
                return phase_name[i];
            }
        }
        return null;
    }

    /*
     * Return the property name given the phase number
     */
    static public String property(int number) {
        for (int i=0; i<phase_number.length; i++) {
            if (phase_number[i] == number) {
                return phase_property_name[i];
            }
        }
        return null;
    }
    /*
     * Return the property name given the phase name
     */
    static public String property(String name) {
         for (int i=0; i<phase_name.length; i++) {
            if (phase_name[i].equalsIgnoreCase(name)) {
                return phase_property_name[i];
            }
        }
        return null;
    }


    /*
     * Return the HTML code given the phase number
     */
    static public String htmlCode(int number) {
        for (int i=0; i<phase_number.length; i++) {
            if (phase_number[i] == number) {
                return phase_html_code[i];
            }
        }
        return null;
    }
    
    /*
     * Return the HTML code given the phase name
     */
    static public String htmlCode(String name) {
         for (int i=0; i<phase_name.length; i++) {
            if (phase_name[i].equalsIgnoreCase(name)) {
                return phase_html_code[i];
            }
        }
        return null;
    }
    
    /***
     *
     *   Some of the phase numbers:
     *   --------------
     *   1- Cement and (random) calcium sulfate
     *   2- C2S
     *   7- Dihydrate (gypsum)
     *   8- hemihydrate
     *   9- anhydrite
     *   10- Silica fume
     *   11- Inert
     *   12- Slag
     *   33- CaCO3
     *   18- Fly Ash
     *   37- Lime
     *
     **/
    
    static private int[] phase_number =
    { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
      21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38 };

    static private String[] phase_name =
    { "C3S", "C2S", "C3A", "C4AF", "K2SO4", "Na2SO4", "Dihydrate",
      "Hemihydrate", "Anhydrite", "Silica Fume", "Inert Filler", "Slag",
      "Inert Aggregate", "AS Glass", "CAS2", "Amorph. SiO2", "FAC3A",
      "Fly Ash", "CH", "C-S-H", "C3AH6", "Ettringite", "C4AF Ettr.",
      "AFm", "FH3", "Pozz. C-S-H", "Slag C-S-H", "CaCl2", "Friedel Salt",
      "Stratlingite", "Secondary Gypsum", "Absorbed Gypsum", "CaCO3",
      "Monocarboaluminate", "Brucite", "MS", "Free Lime", "Orth. C3A" };
    
    static private String[] phase_property_name =
    { "c3s", "c2s", "c3a", "c4af", "k2so4", "na2so4", "dihydrate",
      "hemihydrate", "anhydrite", "silica_fume", "inert_filler", "slag",
      "inert_aggregate", "as_glass", "cas2", "amorph_sio2", "FAC3A",
      "fly_ash", "ch", "c-s-h", "c3ah6", "ettringite", "c4af_ettr", "afm",
      "fh3", "pozz_c-s-h", "slag_c-s-h", "cacl2", "friedel_salt", "stratlingite",
      "secondary_gypsum", "absorbed_gypsum", "caco3", "monocarboaluminate",
      "brucite", "ms", "free_lime", "orth_c3a" };
    
    static private String[] phase_html_code =
    { "C<SUB>3</SUB>S", "C<SUB>2</SUB>S", "C<SUB>3</SUB>A", "C<SUB>4</SUB>AF",
      "K<SUB>2</SUB>SO<SUB>4</SUB>", "Na<SUB>2</SUB>SO<SUB>4</SUB>",
      "Dihydrate", "Hemihydrate", "Anhydrite", "Silica Fume", "Inert Filler",
      "Slag", "Inert Aggregate", "AS Glass", "CAS<SUB>2</SUB>", "Amorph. SiO<SUB>2</SUB>",
      "FAC<SUB>3</SUB>A", "Fly ash", "CH", "C-S-H", "C<SUB>3</SUB>AH<SUB>6</SUB>",
      "Ettringite", "C<SUB>4</SUB>AF Ettr.", "AFm", "FH<SUB>3</SUB>", "Pozz. C-S-H",
      "Slag C-S-H", "CaCl<SUB>2</SUB>", "Friedel Salt", "Stratlingite", "Secondary Gypsum",
      "Absorbed Gypsum", "CaCO<SUB>3</SUB>", "Monocarboaluminate", "Brucite", "MS",
      "Free Lime", "Orth. C<SUB>3</SUB>A" };
}
