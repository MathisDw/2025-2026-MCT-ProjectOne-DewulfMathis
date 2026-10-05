## 4. Hoe kalibreer je de weegschaal?

`kalibratie_factor = 1.0 `

Nu krijg je de "ruwe" waarden. Om dit om te zetten naar grammen of kilo's, doe je het volgende:

1. Zorg dat de weegschaal leeg is en start het script. Hij zet de waarde nu op 0.

2. Leg een object waarvan je het exacte gewicht weet op de weegschaal (bijvoorbeeld een pak suiker van exact 1000 gram).

3. Kijk welk getal er op je scherm verschijnt. Stel, je legt er 1000 gram op en het scherm toont 400000.

4. Bereken je kalibratiefactor: Ruwe waarde / Bekend gewicht

5. Pas de code aan! Verander regel 31 in het script naar je berekende waarde:
kalibratie_factor = 400

6. Start het script opnieuw. Je weegschaal zal nu netjes 1000 (gram) aangeven!