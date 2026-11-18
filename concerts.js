(() => {
  'use strict';

  const list = document.getElementById('concert-list');
  const message = document.getElementById('concert-message');
  const banner = document.getElementById('concert-demo-note');
  const feedback = document.getElementById('concert-ticket-demo');
  if (!list || !message || !banner || !feedback) return;

  const params = new URLSearchParams(window.location.search);
  const demo = params.get('demo') === '1';
  const demoShows = [
    {date: '2027-05-15', city: 'Liège', country: 'Belgium', ticketUrl: ''},
    {date: '2027-06-22', city: 'Brussels', country: 'Belgium', ticketUrl: ''}
  ];

  function todayInBrussels() {
    // Compare calendar dates, rather than milliseconds, so a concert remains
    // listed throughout the day it takes place.
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Europe/Brussels', year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(new Date());
    const value = type => parts.find(p => p.type === type).value;
    return value('year') + '-' + value('month') + '-' + value('day');
  }

  function validDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const d = new Date(value + 'T12:00:00Z');
    return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === value;
  }

  function ticketUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' ? url.href : '';
    } catch (_) { return ''; }
  }

  function render(shows, isDemo) {
    const today = todayInBrussels();
    const upcoming = shows.filter(s => s && validDate(s.date) &&
      s.date >= today && typeof s.city === 'string' && s.city.trim())
      .sort((a,b) => a.date.localeCompare(b.date) || a.city.localeCompare(b.city));

    list.replaceChildren();
    banner.hidden = !isDemo;
    feedback.hidden = !(isDemo && params.get('ticket-test') === '1');

    if (!upcoming.length) {
      message.textContent = 'NO UPCOMING SHOWS';
      message.hidden = false;
      return;
    }

    message.hidden = true;
    const df = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'UTC', day: '2-digit', month: 'short', year: 'numeric'
    });

    for (const show of upcoming) {
      const article = document.createElement('article');
      article.className = 'concert-row';

      const date = document.createElement('time');
      date.className = 'concert-date';
      date.dateTime = show.date;
      date.textContent = df.format(new Date(show.date + 'T12:00:00Z')).toUpperCase();

      const city = document.createElement('strong');
      city.className = 'concert-city';
      const location = show.city.trim();
      city.textContent = (location + (show.country ? ', ' + show.country.trim() : '')).toUpperCase();

      const link = document.createElement('a');
      link.className = 'concert-ticket';
      link.textContent = 'TICKETS';
      if (isDemo) {
        link.href = 'concerts.html?demo=1&ticket-test=1';
        link.setAttribute('aria-label', 'Test the ticket button — demo only');
      } else {
        const url = ticketUrl(show.ticketUrl);
        if (url) {
          link.href = url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.setAttribute('aria-label', 'Tickets for ' + location + ' concert');
        } else {
          link.replaceWith(document.createElement('span'));
          const unavailable = article.appendChild(document.createElement('span'));
          unavailable.className = 'concert-ticket-unavailable';
          unavailable.textContent = 'TICKETS SOON';
        }
      }
      const info = document.createElement('div');
      info.className = 'concert-info';
      info.append(date, city);
      article.append(info);
      if (isDemo || ticketUrl(show.ticketUrl)) article.append(link);
      list.append(article);
    }
  }

  if (demo) {
    render(demoShows, true);
    return;
  }

  fetch('concerts-data.json?t=' + Date.now(), {cache: 'no-store'})
    .then(response => {
      if (!response.ok) throw new Error('Concert data unavailable');
      return response.json();
    })
    .then(data => {
      if (!data || !Array.isArray(data.concerts)) throw new Error('Invalid concert data');
      render(data.concerts, false);
    })
    .catch(() => {
      list.replaceChildren();
      message.hidden = false;
      message.textContent = 'CONCERT DATES TEMPORARILY UNAVAILABLE';
    });
})();
