/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.Cement;

/**
 *
 * @author mateo
 */
public class CementUploadResult {

    private Cement cement;
    private boolean psdNameAlreadyTaken,  alkaliNameAlreadyTaken;
    private String psdName,  alkaliName, psdDataText, alkaliDataText;

    public CementUploadResult(Cement cement, boolean psdNameAlreadyTaken, boolean alkaliNameAlreadyTaken,
            String psdName, String alkaliName, String psdDataText, String alkaliDataText) {
        this.cement = cement;
        this.psdNameAlreadyTaken = psdNameAlreadyTaken;
        this.alkaliNameAlreadyTaken = alkaliNameAlreadyTaken;
        this.psdName = psdName;
        this.alkaliName = alkaliName;
        this.psdDataText = psdDataText;
        this.alkaliDataText = alkaliDataText;
    }

    public String getAlkaliName() {
        return alkaliName;
    }

    public void setAlkaliName(String alkaliName) {
        this.alkaliName = alkaliName;
    }

    public boolean isAlkaliNameAlreadyTaken() {
        return alkaliNameAlreadyTaken;
    }

    public void setAlkaliNameAlreadyTaken(boolean alkaliNameAlreadyTaken) {
        this.alkaliNameAlreadyTaken = alkaliNameAlreadyTaken;
    }

    public Cement getCement() {
        return cement;
    }

    public void setCement(Cement cement) {
        this.cement = cement;
    }

    public String getPsdName() {
        return psdName;
    }

    public void setPsdName(String psdName) {
        this.psdName = psdName;
    }

    public boolean isPsdNameAlreadyTaken() {
        return psdNameAlreadyTaken;
    }

    public void setPsdNameAlreadyTaken(boolean psdNameAlreadyTaken) {
        this.psdNameAlreadyTaken = psdNameAlreadyTaken;
    }

    public String getPsdDataText() {
        return psdDataText;
    }

    public void setPsdDataText(String psdDataText) {
        this.psdDataText = psdDataText;
    }

    public String getAlkaliDataText() {
        return alkaliDataText;
    }

    public void setAlkaliDataText(String alkaliDataText) {
        this.alkaliDataText = alkaliDataText;
    }
}
