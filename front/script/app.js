'use strict';
const lanIP = `${window.location.hostname}:8000`;
const socketio = io(lanIP);

// #region ***  DOM references                           ***********
const charts = {};
let tarraGewicht = 0;
// #endregion

// #region ***  Callback-Visualisation - show___         ***********
const showLatestDataByDeviceID = (jsonObject, deviceID) => {
  console.log('Latest Data');
  console.log(jsonObject);
  const output = jsonObject.value;
  const htmlLiveDataByDeviceID = document.querySelector(
    `.js-value--live[data-deviceid="${jsonObject.device_id}"]`,
  );

  if (deviceID === 1) {
    const brutoGewicht = output;
    let liters = (brutoGewicht - tarraGewicht) / 1000.0 / 1.05;
    if (liters < 0) {
      liters = 0.0;
    }

    htmlLiveDataByDeviceID.innerHTML = liters.toFixed(3);
  } else {
    htmlLiveDataByDeviceID.innerHTML = output.toFixed(3);
  }
};

const showData = (jsonObject, deviceID) => {
  // console.log(jsonObject);
  // 1. Een lege lijst voor zowel x als y waarden
  let arrDataPoints = [];

  if (deviceID == 1) {
    console.warn(jsonObject)
    for (const historic of jsonObject.history) {
      const brutoGewicht = historic.value;
      console.log(tarraGewicht);
      let liters = ((brutoGewicht - tarraGewicht) / 1000.0 / 1.05).toFixed(3);
      if (liters <= 0) {
        liters = 0;
      }

      console.warn(liters)

      arrDataPoints.push({
        x: historic.tijdstip.replace('T', ' '),
        y: liters,
      });
    }

    const series = [
      {
        name: `Sensor ${deviceID}`,
        data: arrDataPoints,
      },
    ];

    showUpdateChart(series, deviceID);
  } else {
    // 2. Loop door de volledige jsonObject
    for (const historic of jsonObject.history) {
      // 3. Maak een pakketje van de X (tijd) EN Y (value) en stoppen dit in de lijst
      arrDataPoints.push({
        x: historic.tijdstip.replace('T', ' '),
        y: historic.value,
      });
    }

    // 4. Stop deze nieuwe lijst in de series
    const series = [
      {
        name: `Sensor ${deviceID}`,
        data: arrDataPoints,
      },
    ];

    // 5. Teken de chart, geen aparte X en Y waarden meer (alles in series)
    showUpdateChart(series, deviceID);
  }
};

const showDrawChart = (series, deviceID) => {
  const htmlChartByDeviceID = document.querySelector(
    `.js-chart[data-deviceid="${deviceID}"]`,
  );
  htmlChartByDeviceID.innerHTML = null;

  let options = {
    chart: {
      type: 'line',
      // animations: {
      //   enabled: true, // Soepele schuif-animatie
      //   dynamicAnimation: {
      //     enabled: false,
      //   },
      // },
      toolbar: {
        show: false, // Dit verbergt de hele werkbalk
      },
      zoom: {
        enabled: false, // Dit voorkomt het per ongeluk inzoomen tijdens het scrollen
      },
    },
    series: series,
    xaxis: {
      type: 'category',
    },
    stroke: {
      // vorm van de grafiek
      curve: 'straight', // straight (default), smooth, stepline
    },
    markers: {
      // grootte van de bolletjes
      size: 0, // default = 0
    },
  };

  let chart = new ApexCharts(htmlChartByDeviceID, options); // ApexCharts(location, options)

  chart.render();

  charts[deviceID] = chart;
};

const showKegsByDatePeriod = (jsonObject) => {
  console.log(jsonObject);
  let output = '';
  const htmlSelectKeg = document.querySelector('.js-select-keg');

  for (const keg of jsonObject.vaten) {
    output += `<option value="${keg.vat_id}">${keg.naam} - (${keg.aanmaakdatum.replace('T', ' ')})</option>`;
  }

  htmlSelectKeg.innerHTML = output;
  ListenToKegPicker();
};

const showUpdateChart = (jsonObject, deviceID) => {
  console.log('Chart aanvullen...');
  // console.log(jsonObject);
  if (charts[deviceID]) {
    charts[deviceID].updateSeries(jsonObject, true); // true = animatie
  } else {
    console.warn(
      `Kan grafiek ${deviceID} niet updaten, want hij is nog niet getekend.`,
    );
    if (document.querySelector('.js-index-html')) {
      getAllHistoryByDeviceIDAndLatestKeg(deviceID);
    }
  }
};

const showCurrentConfigs = (jsonObject) => {
  const htmlFeedback = document.querySelector('.js-settings-feedback');
  // console.log(jsonObject);

  for (const config of jsonObject.settings) {
    const configID = config.config_id;
    // console.log(configID);
    const htmlInputConfig = document.querySelector(
      `.js-input-config[data-configid="${config.config_id}"]`,
    );
    // console.log(htmlInputConfig);
    htmlInputConfig.value = config.value;
  }

  listenToSaveSettingsButton();
};

const showNewSettings = (json) => {
  const htmlFeedback = document.querySelector('.js-settings-feedback');
  htmlFeedback.classList.remove('u-hide');
  getAllSettings();
};

const showNieuwVatAangemaakt = (jsonObject) => {
  window.location.replace('index.html');
  const htmlIndexTitle = document.querySelector('.js-index-title');
  htmlIndexTitle.innerHTML = 'Nieuwste huidige vat';
};
// #endregion

// #region ***  Callback-No Visualisation - callback___  ***********
// #endregion

// #region ***  Data Access - get___                     ***********
const getLatestDataByDeviceID = async (deviceID) => {
  const url = `http://${lanIP}/api/v1/history/device/${deviceID}/latest`;
  const response = await fetch(url).catch((err) =>
    console.error('Fetch-error:', err),
  );
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  if (json && json.historiek_id) {
    showLatestDataByDeviceID(json, deviceID);
    // showAppendChart(json, deviceID);
  }
};

const getAllHistoryByDeviceIDAndLatestKeg = async (deviceID) => {
  const url = `http://${lanIP}/api/v1/history/device/${deviceID}/vat/latest`;
  const response = await fetch(url).catch((err) =>
    console.error('Fetch-error:', err),
  );
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  if (json && json.history) {
    showData(json, deviceID);
  } else {
    console.warn('Kon grafiekdata niet ophalen');
  }
};

const getKegsByDatePeriod = async (startDatum, eindDatum) => {
  const url = `http://${lanIP}/api/v1/vaten/dates/${startDatum}/${eindDatum}`;
  const response = await fetch(url).catch((err) =>
    console.error('Fetch-error:', err),
  );
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  if (json && json.vaten) {
    showKegsByDatePeriod(json);
  } else {
    console.warn('Geen vaten gevonden');
  }
};

const getAllHistoryByDeviceIDAndKegID = async (kegID, deviceID) => {
  const url = `http://${lanIP}/api/v1/history/device/${deviceID}/vat/${kegID}`;
  const response = await fetch(url).catch((err) =>
    console.error('Fetch-error:', err),
  );
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  if (json && json.history) {
    showData(json, deviceID);
  } else {
    console.warn('Geen data gevonden');
  }
};

const getAllSettings = async () => {
  const url = `http://${lanIP}/api/v1/config`;
  const response = await fetch(url).catch((err) =>
    console.error('Fetch-error:', err),
  );
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  if (json && json.settings) {
    showCurrentConfigs(json);
  } else {
    console.warn('Geen instellingen gevonden');
  }
};

const getPutNewSettings = async () => {
  const body = JSON.stringify({
    ALARM_gewicht: document.querySelector(`.js-input-config[data-configid="1"]`)
      .value,
    ALARM_temp: document.querySelector(`.js-input-config[data-configid="2"]`)
      .value,
    ALARM_druk: document.querySelector(`.js-input-config[data-configid="3"]`)
      .value,
    tarragewicht: document.querySelector(`.js-input-config[data-configid="4"]`)
      .value,
  });

  const url = `http://${lanIP}/api/v1/config`;
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  }).catch((err) => console.error('Fetch-error:', err));
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  if (json && json.settings) {
    showNewSettings(json);
  } else {
    console.warn('Er is iets misgelopen.');
    getAllSettings();
  }
};

const getWeegschaalTarreer = async () => {
  const body = JSON.stringify({});

  const url = `http://${lanIP}/api/v1/weegschaal/tarreer`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  }).catch((err) => console.error('Fetch-error:', err));
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));
};

const getPostNieuwVat = async (vatNaam) => {
  const body = JSON.stringify({
    naam: vatNaam,
  });

  const url = `http://${lanIP}/api/v1/vaten`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  }).catch((err) => console.error('Fetch-error:', err));
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));

  console.error(json);

  if (json && json.vat_id) {
    showNieuwVatAangemaakt();
  }
};

const getStopMetingen = async () => {
  const body = JSON.stringify({});

  const url = `http://${lanIP}/api/v1/history/stop`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  }).catch((err) => console.error('Fetch-error:', err));
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));
};

const getStartMetingen = async () => {
  const body = JSON.stringify({});

  const url = `http://${lanIP}/api/v1/history/start`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  }).catch((err) => console.error('Fetch-error:', err));
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));
};

const getSystemShutdown = async () => {
  const body = JSON.stringify({});

  const url = `http://${lanIP}/api/v1/system/shutdown`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body,
  }).catch((err) => console.error('Fetch-error:', err));
  const json = await response
    .json()
    .catch((err) => console.error('JSON-error:', err));
};
// #endregion

// #region ***  Event Listeners - listenTo___            ***********
const listenToSocket = () => {
  socketio.on('connect', () => {
    console.log('[SocketIO] Verbonden met socket webserver');
  });

  socketio.on('B2F_nieuwe_waarden', (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_nieuwe_waarden \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    getLatestDataByDeviceID(1);
    getLatestDataByDeviceID(2);
    getLatestDataByDeviceID(3);

    getAllHistoryByDeviceIDAndLatestKeg(1); // haal nu opnieuw alle data op van deze sensor, zodat we de grafiek kunnen aanvullen met de nieuwe waarde
    getAllHistoryByDeviceIDAndLatestKeg(2);
    getAllHistoryByDeviceIDAndLatestKeg(3);
  });

  socketio.on('B2F_ALARM_gewicht', async (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_ALARM_gewicht \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    const htmlLiveValue = document.querySelector(
      `.js-value-live-div[data-deviceid="${jsonObject.device_id}"]`,
    );
    htmlLiveValue.classList.add('c-live__waarde--alarm');
  });

  socketio.on('B2F_ALARM_temp', async (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_ALARM_temp \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    const htmlLiveValue = document.querySelector(
      `.js-value-live-div[data-deviceid="${jsonObject.device_id}"]`,
    );
    htmlLiveValue.classList.add('c-live__waarde--alarm');
  });

  socketio.on('B2F_ALARM_druk', async (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_ALARM_druk \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    const htmlLiveValue = document.querySelector(
      `.js-value-live-div[data-deviceid="${jsonObject.device_id}"]`,
    );
    htmlLiveValue.classList.add('c-live__waarde--alarm');
  });

  socketio.on('B2F_ALARM_gewicht_stop', async (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_ALARM_gewicht_stop \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    const htmlLiveValue = document.querySelector(
      `.js-value-live-div[data-deviceid="${jsonObject.device_id}"]`,
    );
    htmlLiveValue.classList.remove('c-live__waarde--alarm');
  });

  socketio.on('B2F_ALARM_temp_stop', async (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_ALARM_temp_stop \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    const htmlLiveValue = document.querySelector(
      `.js-value-live-div[data-deviceid="${jsonObject.device_id}"]`,
    );
    htmlLiveValue.classList.remove('c-live__waarde--alarm');
  });

  socketio.on('B2F_ALARM_druk_stop', async (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_ALARM_druk_stop \nmeegstuurde JSON`,
    );
    // console.log(jsonObject);

    const htmlLiveValue = document.querySelector(
      `.js-value-live-div[data-deviceid="${jsonObject.device_id}"]`,
    );
    htmlLiveValue.classList.remove('c-live__waarde--alarm');
  });

  socketio.on('B2F_tarra_vat', (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_tarra_vat \nmeegstuurde JSON`,
    );
    console.log(jsonObject);
    tarraGewicht = jsonObject.value;
  });
};

const listenToSocketShutdown = () => {
  socketio.on('connect', () => {
    console.log('[SocketIO] Verbonden met socket webserver (shutdown)');
  });

  socketio.on('B2F_system_shutdown', (jsonObject) => {
    console.log(
      `[SocketIO] Boodschap server: B2F_system_shutdown \nmeegstuurde JSON`,
    );
    console.log(jsonObject);
    window.alert(jsonObject.msg);
  });
};

const listenToIndex2NieuwVat = () => {
  const htmlIndex2NieuwVatButton = document.querySelector(
    '.js-index-2-nieuwvat',
  );
  const htmlPopUp = document.querySelector('.js-popup');

  htmlIndex2NieuwVatButton.addEventListener('click', () => {
    htmlPopUp.classList.remove('u-hide');

    listenToIndex2NieuwVatCancel();
    listenToIndex2NieuwVatContinue();
  });
};

const listenToIndex2NieuwVatCancel = () => {
  const htmlPopUp = document.querySelector('.js-popup');
  const htmlPopUpCancel = document.querySelector('.js-popup-btn-cancel');

  htmlPopUpCancel.addEventListener('click', () => {
    htmlPopUp.classList.add('u-hide');

    listenToIndex2NieuwVat();
  });
};

const listenToIndex2NieuwVatContinue = () => {
  const htmlPopUpContinue = document.querySelector('.js-popup-btn-continue');

  htmlPopUpContinue.addEventListener('click', async () => {
    await getStopMetingen();
    await window.location.replace('nieuw_vat.html');
    // Extra code voor metingen stoppen
  });
};

const listenToDatePicker = () => {
  const htmlStartDate = document.querySelector('.js-start-date');
  const htmlEndDate = document.querySelector('.js-end-date');
  const htmlSelectDateButton = document.querySelector('.js-select-date-button');

  htmlSelectDateButton.addEventListener('click', () => {
    console.log('Datums geselecteerd:');
    const startDatum = htmlStartDate.value;
    let eindDatum = htmlEndDate.value;

    if (startDatum && eindDatum) {
      if (eindDatum <= startDatum) {
        eindDatum = startDatum;
        htmlEndDate.value = eindDatum;
      }

      console.log(startDatum, eindDatum);
      getKegsByDatePeriod(startDatum, eindDatum);
    } else {
      console.warn('Geen datums geselecteerd!');
    }
  });
};

const ListenToKegPicker = () => {
  const htmlSelectKeg = document.querySelector('.js-select-keg');
  const htmlSelectKegButton = document.querySelector('.js-select-keg-button');

  htmlSelectKegButton.addEventListener('click', () => {
    console.log('Vat geselecteerd:');
    const kegID = htmlSelectKeg.value;
    console.log(kegID);
    if (kegID) {
      showDrawChart([], 1); // teken een lege chart 1
      showDrawChart([], 2); // teken een lege chart 2
      showDrawChart([], 3); // teken een lege chart 3
      getAllHistoryByDeviceIDAndKegID(kegID, 1); // haal de eerste keer alle data op
      getAllHistoryByDeviceIDAndKegID(kegID, 2);
      getAllHistoryByDeviceIDAndKegID(kegID, 3);
    } else {
      console.warn('Geen geldig vat');
    }
  });
};

const listenToSaveSettingsButton = () => {
  // if (!element.classList.contains('active')) {
  //   // Add the class 'active'
  //   element.classList.add('active');
  // }

  const htmlSaveButton = document.querySelector('.js-save-settings');
  htmlSaveButton.addEventListener('click', () => {
    console.log('Instellingen opslaan...');
    getPutNewSettings();
  });
};

const listenToShutdown = () => {
  const htmlShutdownButton = document.querySelector('.js-poweroff');
  const htmlPopUp = document.querySelector('.js-popup');

  htmlShutdownButton.addEventListener('click', () => {
    htmlPopUp.classList.remove('u-hide');

    listenToShutdownCancel();
    listenToShutdownContinue();
  });
};

const listenToShutdownCancel = () => {
  const htmlPopUp = document.querySelector('.js-popup');
  const htmlPopUpCancel = document.querySelector('.js-popup-btn-cancel');

  htmlPopUpCancel.addEventListener('click', () => {
    htmlPopUp.classList.add('u-hide');

    listenToShutdown();
  });
};

const listenToShutdownContinue = () => {
  const htmlPopUpShutdown = document.querySelector('.js-popup-btn-shutdown');

  htmlPopUpShutdown.addEventListener('click', () => {
    console.warn('Shutting down system...');
    getSystemShutdown();
  });
};

const listenToTareButton = () => {
  const htmlTareButton = document.querySelector('.js-tare-button');

  htmlTareButton.addEventListener('click', () => {
    console.log('Tarreren...');
    getWeegschaalTarreer();
  });
};

const listenToNieuwVatButton = () => {
  const htmlNieuwVatButton = document.querySelector('.js-nieuw-vat-button');

  htmlNieuwVatButton.addEventListener('click', () => {
    console.log('Nieuw vat wordt aangemaakt!');
    const htmlVatNaam = document.querySelector('.js-input-vatnaam');
    const vatNaam = htmlVatNaam.value;
    if (vatNaam) {
      getPostNieuwVat(vatNaam);
      getStartMetingen();
    } else {
      console.warn('Voer eerst een naam in.');
    }
  });
};
// #endregion

// #region ***  Init / DOMContentLoaded                  ***********
const init = async () => {
  const indexHTML = document.querySelector('.js-index-html');
  const historiekHTML = document.querySelector('.js-historiek-html');
  const configHTML = document.querySelector('.js-config-html');
  const nieuwVatHTML = document.querySelector('.js-nieuw-vat-html');

  console.info('init initiated: DOM geladen');
  if (indexHTML) {
    const htmlAllLiveValues = document.querySelectorAll(`.js-value-live-div`);
    for (const liveValue of htmlAllLiveValues) {
      liveValue.classList.remove('c-live__waarde--alarm');
    }

    showDrawChart([], 1); // teken een lege chart 1
    showDrawChart([], 2); // teken een lege chart 2
    showDrawChart([], 3); // teken een lege chart 3

    getAllHistoryByDeviceIDAndLatestKeg(1); // haal de eerste keer alle data op
    getAllHistoryByDeviceIDAndLatestKeg(2);
    getAllHistoryByDeviceIDAndLatestKeg(3);

    listenToIndex2NieuwVat();
    listenToSocketShutdown();
    await listenToSocket();
  } else if (historiekHTML) {
    listenToDatePicker();

    listenToSocketShutdown();
  } else if (configHTML) {
    getAllSettings();
    listenToShutdown();

    listenToSocketShutdown();
  } else if (nieuwVatHTML) {
    listenToTareButton();
    listenToNieuwVatButton();

    listenToSocketShutdown();
  }
};
// #endregion

document.addEventListener('DOMContentLoaded', init);
