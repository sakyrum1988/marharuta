(function () {
  const root = document.querySelector('[data-country-finder]');
  if (!root) return;
  const lang = root.dataset.lang === 'ru' ? 'ru' : 'en';
  const lists = {
    budget: [
      ['Vietnam', 'Вьетнам', 'move-to-vietnam', 'Strong value; verify the legal basis for longer stays.', 'Хорошее соотношение цены и быта; отдельно проверьте основание для долгого проживания.'],
      ['Thailand', 'Таиланд', 'move-to-thailand', 'Broad lifestyle choice and several stay routes.', 'Большой выбор форматов жизни и несколько маршрутов пребывания.'],
      ['Malaysia', 'Малайзия', 'move-to-malaysia', 'Good infrastructure with moderate regional costs.', 'Сильная инфраструктура при умеренных для региона расходах.']
    ],
    career: [
      ['Singapore', 'Сингапур', 'move-to-singapore', 'High-opportunity market with selective work passes.', 'Сильный рынок, но строгий отбор по рабочим разрешениям.'],
      ['Hong Kong', 'Гонконг', 'hong-kong', 'A deep international market for qualified profiles.', 'Международный рынок для квалифицированных специалистов.'],
      ['Japan', 'Япония', 'japan', 'Large specialist market; role and language matter.', 'Большой рынок специалистов; критичны роль и язык.']
    ],
    family: [
      ['Malaysia', 'Малайзия', 'move-to-malaysia', 'English-friendly services and practical city options.', 'Англоязычные сервисы и практичный выбор городов.'],
      ['Taiwan', 'Тайвань', 'move-to-taiwan', 'Strong urban services and a professional talent route.', 'Сильные городские сервисы и маршрут для специалистов.'],
      ['Japan', 'Япония', 'japan', 'Safe, structured daily life; budget and language need planning.', 'Безопасный и организованный быт; нужны бюджет и языковой план.']
    ],
    longstay: [
      ['Malaysia', 'Малайзия', 'move-to-malaysia', 'Published long-stay options; check current conditions.', 'Есть опубликованные long-stay программы; сверяйте условия.'],
      ['Thailand', 'Таиланд', 'move-to-thailand', 'Multiple long-stay categories for different profiles.', 'Несколько категорий для разных долгосрочных сценариев.'],
      ['Taiwan', 'Тайвань', 'move-to-taiwan', 'A credible talent-led route for qualified applicants.', 'Понятный talent-маршрут для подходящих специалистов.']
    ]
  };
  const render = () => {
    const selected = root.querySelector('input[name="priority"]:checked');
    const results = root.querySelector('[data-results]');
    results.innerHTML = lists[selected ? selected.value : 'budget'].map((item, index) => {
      const name = lang === 'ru' ? item[1] : item[0];
      const note = lang === 'ru' ? item[4] : item[3];
      const prefix = lang === 'ru' ? '/ru' : '';
      return `<article class="ep-card"><p class="ep-section-label">#${index + 1}</p><h3>${name}</h3><p>${note}</p><a href="${prefix}/countries/${item[2]}/">${lang === 'ru' ? 'Открыть гид' : 'Open guide'} →</a></article>`;
    }).join('');
    results.classList.add('ep-grid');
  };
  root.querySelector('[data-find]').addEventListener('click', render);
  render();
}());
