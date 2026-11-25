PROGRAM PLC_PRG
VAR
    // Fyysiset/simulaation tulot (Inputs)
    bStartButton      : BOOL := FALSE;
    bStopButton       : BOOL := FALSE;
    bEmergencyStop    : BOOL := TRUE;  // Avautuva kosketin (NC)
    bSensorEntry      : BOOL := FALSE; // Kappale saapuu linjalle
    bSensorHighItem   : BOOL := FALSE; // Korkea kappale tunnistettu
    bSensorExitA      : BOOL := FALSE; // Poistumisanturi A (korkeat)
    bSensorExitB      : BOOL := FALSE; // Poistumisanturi B (matalat)

    // Fyysiset/simulaation lähdöt (Outputs)
    bConveyorMain     : BOOL := FALSE;
    bSorterPusherA    : BOOL := FALSE;

    // Sisäiset tilamuuttujat ja ajastimet
    eState            : INT := 0;      // 0=Seis, 10=Käynnissä, 99=Hätäseis
    bItemIsHigh       : BOOL := FALSE;
    tPusherTimer      : TON;

    // OPC UA -rajapintaan jaettavat OEE-muuttujat
    {attribute 'opc.ua.da' := '1'}
    nTotalCount       : DINT := 0;
    {attribute 'opc.ua.da' := '1'}
    nSortedACount     : DINT := 0;
    {attribute 'opc.ua.da' := '1'}
    nSortedBCount     : DINT := 0;
    {attribute 'opc.ua.da' := '1'}
    nSystemState      : INT := 0;
END_VAR

// 1. Turvalogiikka (Hätäseis ohittaa kaiken)
IF NOT bEmergencyStop THEN
    eState := 99;
    bConveyorMain := FALSE;
    bSorterPusherA := FALSE;
END_IF;

// 2. Tilakone (State Machine)
CASE eState OF
    0: // VALMIUSTILA (IDLE)
        bConveyorMain := FALSE;
        bSorterPusherA := FALSE;
        IF bStartButton AND bEmergencyStop THEN
            eState := 10;
        END_IF;

    10: // TUOTANTO KÄYNNISSÄ (RUNNING)
        bConveyorMain := TRUE;
        
        // Tunnistetaan korkea kappale
        IF bSensorHighItem THEN
            bItemIsHigh := TRUE;
        END_IF;

        // Ohjataan lajittelusylinteriä, jos kappale on korkea
        tPusherTimer(IN := bItemIsHigh, PT := T#1.5S);
        IF tPusherTimer.Q THEN
            bSorterPusherA := TRUE;
        END_IF;

        // Laskurit kappaleen poistuessa linjalta
        IF bSensorExitA THEN
            nSortedACount := nSortedACount + 1;
            nTotalCount := nTotalCount + 1;
            bItemIsHigh := FALSE;
            bSorterPusherA := FALSE;
        ELSIF bSensorExitB THEN
            nSortedBCount := nSortedBCount + 1;
            nTotalCount := nTotalCount + 1;
        END_IF;

        IF bStopButton THEN
            eState := 0;
        END_IF;

    99: // HÄTÄSEIS (EMERGENCY STOP)
        IF bEmergencyStop AND bStopButton THEN
            eState := 0; // Kuittaus Stop-napilla
        END_IF;
END_CASE;

nSystemState := eState;