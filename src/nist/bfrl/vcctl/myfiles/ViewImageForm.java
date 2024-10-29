/*
 * ViewImageForm.java
 *
 * Created on February 13, 2006, 10:30 AM
 */

package nist.bfrl.vcctl.myfiles;


/**
 *
 * @author tahall
 * @version
 */

public class ViewImageForm extends org.apache.struts.action.ActionForm {
    
    private String name;
    
    /**
     * @return
     */
    public String getName() {
        return name;
    }
    
    /**
     * @param string
     */
    public void setName(String string) {
        name = string;
    }



    /**
     * Constructor
     */
    public ViewImageForm() {
        super();
        
        reset();
    }
    
    public void reset() {
        this.setName("");
        this.setMagnification("5");
        this.setPlane("yz");
        this.setSliceNumber("50");
        this.setViewdepth("no");
        this.setBse("no");
        this.setOptype("");
    }
    
    /**
     * Holds value of property plane.
     */
    private String plane;
    
    /**
     * Getter for property plane.
     * @return Value of property plane.
     */
    public String getPlane() {
        return this.plane;
    }
    
    /**
     * Setter for property plane.
     * @param plane New value of property plane.
     */
    public void setPlane(String plane) {
        this.plane = plane;
    }
    
    /**
     * Holds value of property sliceNumber.
     */
    private String sliceNumber;
    
    /**
     * Getter for property slice.
     * @return Value of property slice.
     */
    public String getSliceNumber() {
        return this.sliceNumber;
    }
    
    /**
     * Setter for property slice.
     * @param slice New value of property slice.
     */
    public void setSliceNumber(String sliceNumber) {
        this.sliceNumber = sliceNumber;
    }
    
    /**
     * Holds value of property magnification.
     */
    private String magnification;
    
    /**
     * Getter for property magnification.
     * @return Value of property magnification.
     */
    public String getMagnification() {
        return this.magnification;
    }
    
    /**
     * Setter for property magnification.
     * @param magnification New value of property magnification.
     */
    public void setMagnification(String magnification) {
        this.magnification = magnification;
    }

    /**
     * Holds value of property viewdepth.
     */
    private String viewdepth;

    /**
     * Getter for property viewdepth.
     * @return Value of property viewdepth.
     */
    public String getViewdepth() {
        return this.viewdepth;
    }

    /**
     * Setter for property viewdepth.
     * @param viewdepth New value of property viewdepth.
     */
    public void setViewdepth(String viewdepth) {
        this.viewdepth = viewdepth;
    }

     /**
     * Holds value of property bse.
     */
    private String bse;

    /**
     * Getter for property bse.
     * @return Value of property bse.
     */
    public String getBse() {
        return this.bse;
    }

    /**
     * Setter for property bse.
     * @param bse New value of property bse.
     */
    public void setBse(String bse) {
        this.bse = bse;
    }

    /**
     * Holds value of property opname.
     */
    private String opname;

    /**
     * Getter for property opname.
     * @return Value of property opname.
     */
    public String getOpname() {
        return this.opname;
    }

    /**
     * Setter for property opname.
     * @param opname New value of property opname.
     */
    public void setOpname(String opname) {
        this.opname = opname;
    }

    /**
     * Holds value of property optype.
     */
    private String optype;

    /**
     * Getter for property optype.
     * @return Value of property optype.
     */
    public String getOptype() {
        return this.optype;
    }

    /**
     * Setter for property optype.
     * @param optype New value of property optype.
     */
    public void setOptype(String optype) {
        this.optype = optype;
    }



    /**
     * Holds value of property sliceName.
     */
    private String sliceName;

    /**
     * Getter for property sliceName.
     * @return Value of property sliceName.
     */
    public String getSliceName() {
        return this.sliceName;
    }

    /**
     * Setter for property sliceName.
     * @param sliceName New value of property sliceName.
     */
    public void setSliceName(String sliceName) {
        this.sliceName = sliceName;
    }
    
}
