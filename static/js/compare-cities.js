(function () {
  var CITIES = [
    { label: 'Bangkok',        country: 'Thailand',     slug: 'bangkok' },
    { label: 'Chiang Mai',     country: 'Thailand',     slug: 'chiang-mai' },
    { label: 'Kuala Lumpur',   country: 'Malaysia',     slug: 'kuala-lumpur' },
    { label: 'Singapore',      country: 'Singapore',    slug: 'singapore' },
    { label: 'Ho Chi Minh City', country: 'Vietnam',   slug: 'ho-chi-minh-city' },
    { label: 'Jakarta',        country: 'Indonesia',    slug: 'jakarta' },
    { label: 'Taipei',         country: 'Taiwan',       slug: 'taipei' },
    { label: 'Tokyo',          country: 'Japan',        slug: 'tokyo' },
    { label: 'Seoul',          country: 'South Korea',  slug: 'seoul' },
    { label: 'Manila',         country: 'Philippines',  slug: 'manila' },
    { label: 'Hong Kong',      country: 'China SAR',    slug: 'hong-kong' }
  ];

  var DATA = {
    'bangkok': {
      score: 52.5,
      cats: {
        'Housing': 3.5, 'Cost of Living': 6.5, 'Safety': 5.0, 'Healthcare': 5.5,
        'Internet Access': 5.0, 'Startups': 5.5, 'Business Freedom': 6.0, 'Taxation': 7.5,
        'Leisure & Culture': 8.0, 'Outdoors': 5.0, 'Tolerance': 5.5,
        'Education': 4.5, 'Economy': 5.0, 'Travel Connectivity': 8.5,
        'Environmental Quality': 3.0, 'Commute': 3.0
      }
    },
    'chiang-mai': {
      score: 56.5,
      cats: {
        'Housing': 6.5, 'Cost of Living': 8.5, 'Safety': 7.0, 'Healthcare': 5.0,
        'Internet Access': 5.5, 'Startups': 4.0, 'Business Freedom': 6.5, 'Taxation': 7.5,
        'Leisure & Culture': 6.5, 'Outdoors': 8.0, 'Tolerance': 7.0,
        'Education': 3.5, 'Economy': 4.0, 'Travel Connectivity': 5.0,
        'Environmental Quality': 4.5, 'Commute': 6.5
      }
    },
    'kuala-lumpur': {
      score: 57.2,
      cats: {
        'Housing': 5.0, 'Cost of Living': 6.5, 'Safety': 5.5, 'Healthcare': 6.5,
        'Internet Access': 6.0, 'Startups': 5.0, 'Business Freedom': 6.5, 'Taxation': 7.0,
        'Leisure & Culture': 7.0, 'Outdoors': 5.5, 'Tolerance': 5.5,
        'Education': 6.0, 'Economy': 6.0, 'Travel Connectivity': 7.5,
        'Environmental Quality': 4.5, 'Commute': 4.0
      }
    },
    'singapore': {
      score: 72.0,
      cats: {
        'Housing': 2.0, 'Cost of Living': 2.5, 'Safety': 9.5, 'Healthcare': 9.0,
        'Internet Access': 9.5, 'Startups': 9.0, 'Business Freedom': 9.5, 'Taxation': 7.5,
        'Leisure & Culture': 7.5, 'Outdoors': 6.5, 'Tolerance': 7.5,
        'Education': 9.0, 'Economy': 9.5, 'Travel Connectivity': 9.5,
        'Environmental Quality': 7.0, 'Commute': 7.0
      }
    },
    'ho-chi-minh-city': {
      score: 49.5,
      cats: {
        'Housing': 5.5, 'Cost of Living': 8.0, 'Safety': 5.0, 'Healthcare': 4.0,
        'Internet Access': 5.5, 'Startups': 4.5, 'Business Freedom': 4.5, 'Taxation': 6.5,
        'Leisure & Culture': 7.0, 'Outdoors': 4.5, 'Tolerance': 5.0,
        'Education': 4.0, 'Economy': 6.0, 'Travel Connectivity': 6.5,
        'Environmental Quality': 3.5, 'Commute': 3.5
      }
    },
    'jakarta': {
      score: 46.5,
      cats: {
        'Housing': 4.0, 'Cost of Living': 7.0, 'Safety': 4.5, 'Healthcare': 4.5,
        'Internet Access': 4.5, 'Startups': 5.0, 'Business Freedom': 5.0, 'Taxation': 5.5,
        'Leisure & Culture': 6.0, 'Outdoors': 4.5, 'Tolerance': 5.5,
        'Education': 4.5, 'Economy': 5.5, 'Travel Connectivity': 7.0,
        'Environmental Quality': 3.0, 'Commute': 2.5
      }
    },
    'taipei': {
      score: 65.0,
      cats: {
        'Housing': 4.0, 'Cost of Living': 5.5, 'Safety': 8.5, 'Healthcare': 8.5,
        'Internet Access': 9.0, 'Startups': 6.5, 'Business Freedom': 7.0, 'Taxation': 6.5,
        'Leisure & Culture': 7.5, 'Outdoors': 7.0, 'Tolerance': 7.5,
        'Education': 7.5, 'Economy': 7.0, 'Travel Connectivity': 6.5,
        'Environmental Quality': 5.0, 'Commute': 6.5
      }
    },
    'tokyo': {
      score: 66.8,
      cats: {
        'Housing': 3.5, 'Cost of Living': 4.0, 'Safety': 9.5, 'Healthcare': 8.5,
        'Internet Access': 9.0, 'Startups': 6.0, 'Business Freedom': 6.5, 'Taxation': 5.0,
        'Leisure & Culture': 9.0, 'Outdoors': 7.0, 'Tolerance': 5.5,
        'Education': 8.0, 'Economy': 8.0, 'Travel Connectivity': 9.0,
        'Environmental Quality': 6.5, 'Commute': 7.5
      }
    },
    'seoul': {
      score: 67.0,
      cats: {
        'Housing': 3.0, 'Cost of Living': 4.5, 'Safety': 8.0, 'Healthcare': 8.5,
        'Internet Access': 8.5, 'Startups': 7.5, 'Business Freedom': 7.0, 'Taxation': 5.5,
        'Leisure & Culture': 8.5, 'Outdoors': 6.5, 'Tolerance': 6.0,
        'Education': 8.5, 'Economy': 8.0, 'Travel Connectivity': 8.5,
        'Environmental Quality': 5.5, 'Commute': 7.0
      }
    },
    'manila': {
      score: 44.0,
      cats: {
        'Housing': 6.0, 'Cost of Living': 7.5, 'Safety': 4.5, 'Healthcare': 4.5,
        'Internet Access': 4.0, 'Startups': 4.0, 'Business Freedom': 5.5, 'Taxation': 5.5,
        'Leisure & Culture': 6.0, 'Outdoors': 5.5, 'Tolerance': 6.5,
        'Education': 4.5, 'Economy': 4.5, 'Travel Connectivity': 5.5,
        'Environmental Quality': 3.0, 'Commute': 2.0
      }
    },
    'hong-kong': {
      score: 68.5,
      cats: {
        'Housing': 1.5, 'Cost of Living': 2.5, 'Safety': 8.5, 'Healthcare': 8.5,
        'Internet Access': 9.0, 'Startups': 8.0, 'Business Freedom': 9.0, 'Taxation': 9.0,
        'Leisure & Culture': 8.5, 'Outdoors': 7.5, 'Tolerance': 7.0,
        'Education': 8.5, 'Economy': 9.0, 'Travel Connectivity': 9.0,
        'Environmental Quality': 5.5, 'Commute': 6.5
      }
    }
  };

  var GROUPS = [
    { label: 'Cost & Housing',  cats: ['Housing', 'Cost of Living'] },
    { label: 'Safety & Health', cats: ['Safety', 'Healthcare'] },
    { label: 'Digital Nomad',   cats: ['Internet Access', 'Startups', 'Business Freedom', 'Taxation'] },
    { label: 'Lifestyle',       cats: ['Leisure & Culture', 'Outdoors', 'Tolerance'] },
    { label: 'Infrastructure',  cats: ['Education', 'Economy', 'Travel Connectivity', 'Environmental Quality', 'Commute'] }
  ];

  function scoreColor(v) {
    if (v >= 7.5) return '#16a34a';
    if (v >= 5)   return '#1a56db';
    if (v >= 3)   return '#ea580c';
    return '#dc2626';
  }

  function render(s1, s2) {
    var d1 = DATA[s1], d2 = DATA[s2];
    var c1 = CITIES.find(function (c) { return c.slug === s1; });
    var c2 = CITIES.find(function (c) { return c.slug === s2; });
    if (!d1 || !d2) return;

    var html = '<div class="cc-city-heads">';
    html += '<div class="cc-lbl-empty"></div>';
    html += '<div class="cc-city-head">'
          + '<strong>' + c1.label + '</strong>'
          + '<br><span style="font-size:12px;color:#888">' + c1.country + '</span>'
          + '<div class="cc-city-head-score" style="color:' + scoreColor(d1.score / 10) + '">' + d1.score + '</div>'
          + '<span style="font-size:11px;color:#888">Overall Score</span>'
          + '</div>';
    html += '<div class="cc-city-head">'
          + '<strong>' + c2.label + '</strong>'
          + '<br><span style="font-size:12px;color:#888">' + c2.country + '</span>'
          + '<div class="cc-city-head-score" style="color:' + scoreColor(d2.score / 10) + '">' + d2.score + '</div>'
          + '<span style="font-size:11px;color:#888">Overall Score</span>'
          + '</div>';
    html += '</div>';

    GROUPS.forEach(function (g) {
      html += '<div class="cc-group-lbl">' + g.label + '</div>';
      g.cats.forEach(function (cat) {
        var v1 = d1.cats[cat] || 0, v2 = d2.cats[cat] || 0;
        var w1 = v1 > v2, w2 = v2 > v1;
        html += '<div class="cc-row">'
              + '<div class="cc-row-lbl">' + cat + '</div>'
              + '<div class="cc-card' + (w1 ? ' winner' : '') + '">'
              +   '<div style="font-size:20px;font-weight:800;color:' + scoreColor(v1) + '">'
              +     v1.toFixed(1) + '<span style="font-size:11px;color:#888">/10</span>'
              +   '</div>'
              +   '<div class="cc-bar-wrap"><div class="cc-bar" style="width:' + (v1 * 10) + '%;background:' + scoreColor(v1) + '"></div></div>'
              + '</div>'
              + '<div class="cc-card' + (w2 ? ' winner' : '') + '">'
              +   '<div style="font-size:20px;font-weight:800;color:' + scoreColor(v2) + '">'
              +     v2.toFixed(1) + '<span style="font-size:11px;color:#888">/10</span>'
              +   '</div>'
              +   '<div class="cc-bar-wrap"><div class="cc-bar" style="width:' + (v2 * 10) + '%;background:' + scoreColor(v2) + '"></div></div>'
              + '</div>'
              + '</div>';
      });
    });

    var el = document.getElementById('cc-results');
    el.innerHTML = html;
    el.classList.add('visible');
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!document.querySelector('.cc-page')) return;

    var sel1 = document.getElementById('cc-city1');
    var sel2 = document.getElementById('cc-city2');
    if (!sel1 || !sel2) return;

    CITIES.forEach(function (c) {
      var o1 = new Option(c.label + ' (' + c.country + ')', c.slug);
      var o2 = new Option(c.label + ' (' + c.country + ')', c.slug);
      sel1.add(o1);
      sel2.add(o2);
    });

    sel2.selectedIndex = 3; // default: Singapore

    function onChange() {
      var s1 = sel1.value, s2 = sel2.value;
      if (s1 && s2 && s1 !== s2) render(s1, s2);
    }

    sel1.addEventListener('change', onChange);
    sel2.addEventListener('change', onChange);
    onChange(); // render on load with defaults
  });
})();
