/*
 * ViewHydrationMovieForm.java
 *
 * Created on November 6, 2013, 1:31 PM
 */

package nist.bfrl.vcctl.myfiles;


/**
 *
 * @author bullard
 * @version
 */

public class ViewHydrationMovieForm extends org.apache.struts.action.ActionForm {
    
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
    public ViewHydrationMovieForm() {
        super();
        
        reset();
    }
    
    public void reset() {
        this.setName("");
        this.setMagnification("5");
        this.setBse("no");
        this.setFramespeed("100");
        this.setOptype("");
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
     * Holds value of property framespeed.
     */
    private String framespeed;

    /**
     * Getter for property framespeed.
     * @return Value of property framespeed.
     */
    public String getFramespeed() {
        return this.framespeed;
    }

    /**
     * Setter for property framespeed.
     * @param framespeed New value of property framespeed.
     */
    public void setFramespeed(String framespeed) {
        this.framespeed = framespeed;
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
     * Holds value of property movieName.
     */
    private String movieName;

    /**
     * Getter for property movieName.
     * @return Value of property movieName.
     */
    public String getMovieName() {
        return this.movieName;
    }

    /**
     * Setter for property movieName.
     * @param movieName New value of property movieName.
     */
    public void setMovieName(String movieName) {
        this.movieName = movieName;
    }
    
}
