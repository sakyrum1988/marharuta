"""Adapt imported tool scripts without modifying the editorial database."""
import re


def harden_tool_scripts(content: str) -> str:
    # Localization must not translate the control identifier used by JavaScript.
    content = content.replace('cc-образ жизни', 'cc-lifestyle')
    def replace_script(match: re.Match) -> str:
        script = match.group(2)
        if 'async function fetchRestCountries(code)' in script:
            script = re.sub(
                r'async function fetchRestCountries\(code\)\{.*?\n\}',
                'async function fetchRestCountries(code){return RtaData.country(code);}',
                script, flags=re.S,
            )
            script = re.sub(
                r'async function fetchClimate\(lat,lon\)\{.*?\n\}',
                'async function fetchClimate(lat,lon){return RtaData.climate(lat,lon);}',
                script, flags=re.S,
            )
            for number in ('1', '2'):
                for field, variable in (('population', 'pop'), ('area', 'area')):
                    script = re.sub(
                        rf'const {variable}{number}=.*?;',
                        f'const {variable}{number}=RtaData.countryValue(rc{number},"{field}");',
                        script,
                    )
        if 'https://open.er-api.com/v6/latest/USD' in script:
            script = re.sub(
                r'fetch\("https://open.er-api.com/v6/latest/USD"\)\s*\.then\(function\(r\)\{return r.json\(\);\}\)',
                'RtaData.rates()', script,
            )
            script = script.replace('RATES[c]||1', 'RtaData.rate(RATES,c)')
            script = script.replace('RATES[cur]||1', 'RtaData.rate(RATES,cur)')
            script = script.replace('toLocaleDateString("en-GB"', 'toLocaleDateString(RtaData.locale')
            script = script.replace('function calc(){', 'function calc(quiet){')
            script = script.replace('re.scrollIntoView(', 'if(quiet!==true)re.scrollIntoView(')
            script = script.replace('res.scrollIntoView(', 'if(quiet!==true)res.scrollIntoView(')
            if 'cc-cur-select' in script:
                script = script.replace('v=u*r;if', 'v=u*r;if(r===null)return "$"+Math.round(u).toLocaleString()+" USD";if')
                script = re.sub(r'function showRate\(\)\{[^\n]*\}', '''function showRate(){
  var c=cur(),r=RtaData.rate(RATES,c),e=g("cc-rate-display");
  if(e)e.textContent=r===null?RtaData.unavailable:"1 USD = "+r.toLocaleString(RtaData.locale,{maximumFractionDigits:4})+" "+c;
}''', script)
                script = script.replace('RATES.USD=1;showRate();', 'RATES.USD=1;showRate();if(g("cc-result")&&g("cc-result").classList.contains("show"))calc(true);')
                script = script.replace('e.textContent="unavailable"', 'e.textContent=RtaData.unavailable')
                # Index 0 is a valid budget choice, not a missing selection.
                for key in ('aM[ac?ac.value:"mid"]', 'fM[fo?fo.value:"mix"]', 'lM[li?li.value:"social"]'):
                    script = script.replace(key+'||1', key+'??1')
                script = script.replace('  RtaData.rates()', '  showRate();\n  RtaData.rates()')
            else:
                script = re.sub(r'// Fetch live rates.*?function fmtUSD', '''var ratesDate = "";
function showRate(){
  var selected=document.getElementById("bp-country-sel");
  var cur=selected&&C[selected.value]?C[selected.value].currency:"USD";
  var rate=RtaData.rate(RATES,cur), el=document.getElementById("bp-rate-info");
  if(el)el.textContent=rate===null?RtaData.unavailable:
    "1 USD = "+rate.toLocaleString(RtaData.locale,{maximumFractionDigits:4})+" "+cur+(ratesDate?" · "+RtaData.asOf+ratesDate:"");
}
RtaData.rates().then(function(data){
  RATES=data.rates;
  ratesDate=new Date(data.time_last_update_utc).toLocaleDateString(RtaData.locale);
  showRate();
  var result=document.getElementById("bp-result");
  if(result&&result.classList.contains("show"))calc(true);
}).catch(function(){
  var el=document.getElementById("bp-rate-info");
  if(el)el.textContent=RtaData.unavailable;
});

function fmtUSD''', script, flags=re.S)
                script = script.replace('val=v*rate;', 'val=v*rate;\n  if(rate===null)return fmtUSD(v)+" USD";')
                script = re.sub(r'  // Update rate badge with local currency.*?\n\}', '  showRate();\n}', script, flags=re.S)
                script = script.replace('if(localEl&&cur!=="USD")', 'if(localEl&&cur!=="USD"&&RtaData.rate(RATES,cur)!==null)')
                script = script.replace('cur&&cur!=="USD"?', 'cur&&cur!=="USD"&&RtaData.rate(RATES,cur)!==null?')
                script = script.replace('function init(){', 'function init(){\n  showRate();')
        return match.group(1) + script + match.group(3)

    return re.sub(r'(<script\b[^>]*>)(.*?)(</script>)', replace_script, content, flags=re.S | re.I)
