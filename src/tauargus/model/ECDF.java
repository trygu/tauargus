/*
* Argus Open Source
* Software to apply Statistical Disclosure Control techniques
* 
* Copyright 2014 Statistics Netherlands
* 
* This program is free software; you can redistribute it and/or 
* modify it under the terms of the European Union Public Licence 
* (EUPL) version 1.1, as published by the European Commission.
* 
* You can find the text of the EUPL v1.1 on
* https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
* 
* This software is distributed on an "AS IS" basis without 
* warranties or conditions of any kind, either express or implied.
*/
package tauargus.model;

public class ECDF {
    private double[] breaks;
    private int[] counts;
    
    public ECDF(int npoints){
        breaks = new double[npoints]; 
        counts = new int[npoints]; 
    }
    
    public void setBreaks(double[] arr){
        this.breaks = arr;
    }

    public void setCounts(int[] arr){
        this.counts = arr;
    }
    
    public double[] getBreaks(){
        return this.breaks;
    }

    public int[] getCounts(){
        return this.counts;
    }

}
