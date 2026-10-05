from repositories.Database import Database


class DataRepository:
    
    @staticmethod
    def create_new_historiek(value, device_id, vat_id):
        sql = "INSERT INTO tblhistoriek (Value, DeviceID, VatID) VALUES (%s, %s, %s)"
        params = [value, device_id, vat_id]
        return Database.execute_sql(sql, params)
    
    @staticmethod
    def read_latest_data_by_device(device_id):
        sql = "SELECT HistoriekID, Tijdstip, Value, DeviceID, VatID FROM tblhistoriek WHERE DeviceID = %s AND \
            Tijdstip = (SELECT MAX(Tijdstip) FROM tblhistoriek WHERE DeviceID = %s)"
        params = [device_id, device_id]
        return Database.get_one_row(sql, params)
    
    @staticmethod
    def read_history_by_device_and_keg(device_id, vat_id):
        sql = "SELECT HistoriekID, Tijdstip, Value, DeviceID, VatID FROM tblhistoriek WHERE DeviceID = %s AND VatID = %s ORDER BY Tijdstip"
        params = [device_id, vat_id]
        return Database.get_rows(sql, params)
    
    @staticmethod
    def read_history_by_device_and_latest_keg(device_id):
        sql = "SELECT HistoriekID, Tijdstip, Value, DeviceID, VatID FROM tblhistoriek WHERE DeviceID = %s AND \
            VatID = (SELECT VatID FROM tblvaten ORDER BY VatID DESC LIMIT 1) ORDER BY Tijdstip"
        params = [device_id]
        return Database.get_rows(sql, params)
    
    @staticmethod
    def read_history_by_id(id):
        sql = "SELECT HistoriekID, Tijdstip, Value, DeviceID, VatID from tblhistoriek WHERE HistoriekID = %s"
        params = [id]
        return Database.get_one_row(sql, params)
    
    @staticmethod
    def create_new_keg(vat_naam):
        sql = "INSERT INTO tblvaten (VatNaam) VALUES (%s)"
        params = [vat_naam]
        return Database.execute_sql(sql, params)
    
    @staticmethod
    def read_keg_by_id(id):
        sql = "SELECT VatID, VatNaam FROM tblvaten WHERE VatID = %s"
        params = [id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_keg_latest():
        sql = "SELECT VatID, VatNaam FROM tblvaten ORDER BY VatID DESC LIMIT 1"
        params = []
        return Database.get_one_row(sql, params)
    
    @staticmethod
    def read_kegs_between_dates(start_date, end_date):
        sql = "SELECT v.VatID, v.VatNaam, MIN(h.Tijdstip) AS Aanmaakdatum FROM tblvaten v JOIN tblhistoriek h ON v.VatID = h.VatID \
        GROUP BY v.VatID, v.VatNaam HAVING DATE(MIN(h.Tijdstip)) >= %s AND DATE(MIN(h.Tijdstip)) <= %s"
        params = [start_date, end_date]
        return Database.get_rows(sql, params)
    
    @staticmethod
    def read_all_configurations():
        sql = "SELECT ConfigID, ConfigNaam, Value, SensorID FROM tblconfig"
        return Database.get_rows(sql)
    
    @staticmethod
    def update_all_configurations(alarm_gewicht, alarm_temp, alarm_druk, tarra):
        sql = "UPDATE tblconfig SET Value = CASE ConfigID \
            WHEN 1 THEN %s \
            WHEN 2 THEN %s \
            WHEN 3 THEN %s \
            WHEN 4 THEN %s \
            END WHERE ConfigID IN (1, 2, 3, 4)"
        params = [alarm_gewicht, alarm_temp, alarm_druk, tarra]
        return Database.execute_sql(sql, params)
    
    # @staticmethod
    # def read_status_lampen():
    #     sql = "SELECT * from lampen"
    #     return Database.get_rows(sql)

    # @staticmethod
    # def read_status_lamp_by_id(id):
    #     sql = "SELECT * from lampen WHERE id = %s"
    #     params = [id]
    #     return Database.get_one_row(sql, params)

    # @staticmethod
    # def update_status_lamp(id, status):
    #     sql = "UPDATE lampen SET status = %s WHERE id = %s"
    #     params = [status, id]
    #     return Database.execute_sql(sql, params)

    # @staticmethod
    # def update_status_alle_lampen(status):
    #     sql = "UPDATE lampen SET status = %s"
    #     params = [status]
    #     return Database.execute_sql(sql, params)

