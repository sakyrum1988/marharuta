/* Shared, bounded requests for the imported interactive tools. */
(function () {
  'use strict';
  const ru = document.documentElement.lang === 'ru';
  let ratesPromise;
  async function json(url) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, {signal: controller.signal});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }
  function rate(rates, currency) {
    if (currency === 'USD') return 1;
    const value = rates[currency];
    return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : null;
  }
  function rates() {
    if (!ratesPromise) {
      ratesPromise = json('https://open.er-api.com/v6/latest/USD').then(data => {
        if (!data || data.result !== 'success' || data.base_code !== 'USD' ||
            !data.rates || data.rates.USD !== 1 ||
            !Number.isFinite(data.time_last_update_unix) ||
            Date.now() / 1000 - data.time_last_update_unix > 3 * 86400 ||
            data.time_last_update_unix > Date.now() / 1000 + 3600) {
          throw new Error('Invalid or outdated exchange rates');
        }
        const valid = {USD: 1};
        for (const currency of Object.keys(data.rates)) {
          if (/^[A-Z]{3}$/.test(currency) && rate(data.rates, currency) !== null) valid[currency] = data.rates[currency];
        }
        if (Object.keys(valid).length < 2) throw new Error('Missing exchange rates');
        return {...data, rates: valid, time_last_update_utc: new Date(data.time_last_update_unix * 1000).toUTCString()};
      }).catch(error => { ratesPromise = null; throw error; });
    }
    return ratesPromise;
  }
  async function country(code) {
    try {
      const data = await json('/api/countries/' + encodeURIComponent(code));
      return data && data.population !== undefined ? data : null;
    } catch (_) { return null; }
  }
  function countryValue(data, field) {
    if (!data || !Number.isFinite(data[field])) return ru ? 'Нет данных' : 'Unavailable';
    const unit = field === 'area' ? (ru ? ' км²' : ' km²') : '';
    const year = data[field + '_year'];
    const vintage = /^\d{4}$/.test(year || '') ? year : (ru ? 'сохранённые данные' : 'saved data');
    return data[field].toLocaleString(ru ? 'ru-RU' : 'en-GB', {maximumFractionDigits:0}) + unit + ' · ' + vintage;
  }
  async function climate(lat, lon) {
    try {
      // Archive observations can lag several days. Use a completed window.
      const end = new Date(Date.now() - 7 * 86400000);
      const start = new Date(end);
      start.setUTCFullYear(start.getUTCFullYear() - 1);
      const params = new URLSearchParams({latitude: lat, longitude: lon,
        start_date: start.toISOString().slice(0, 10), end_date: end.toISOString().slice(0, 10),
        daily: 'temperature_2m_mean,precipitation_sum', timezone: 'auto'});
      const data = await json('https://archive-api.open-meteo.com/v1/archive?' + params);
      if (data.error || !data.daily) return null;
      const temps = (data.daily.temperature_2m_mean || []).filter(Number.isFinite);
      const rain = (data.daily.precipitation_sum || []).filter(Number.isFinite);
      const days = (data.daily.time || []).length;
      if (!days || temps.length < days * .9 || rain.length < days * .9) return null;
      return {
        avgTemp: (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1),
        avgPrecip: (rain.reduce((a, b) => a + b, 0) / rain.length * 365.25 / 12).toFixed(0)
      };
    } catch (_) { return null; }
  }
  window.RtaData = {
    json, rate, rates, country, countryValue, climate,
    unavailable: ru ? 'Курс недоступен. Расчёт показан в USD.' : 'Rate unavailable. Amounts are shown in USD.',
    loading: ru ? 'Загрузка курса; пока расчёт в USD.' : 'Loading rates; amounts currently in USD.',
    asOf: ru ? 'Курсы на ' : 'Rates as of ',
    locale: ru ? 'ru-RU' : 'en-GB'
  };
})();
