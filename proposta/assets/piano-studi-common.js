
(function () {
  const blocks = {
    introduzione: `
      <section>
        <h2>A cosa serve presentare il piano?</h2>
        <p>
          Il piano di studi non serve normalmente per poter sostenere un esame.
          Serve a stabilire <strong>quali attività della tua carriera saranno utilizzate per conseguire la laurea</strong>.
        </p>
        <p>
          Puoi quindi avere in carriera esami che non compaiono ancora in un piano approvato.
          Il piano è il passaggio con cui il Corso di Studio verifica che il percorso che vuoi utilizzare per laurearti
          rispetti le regole previste.
        </p>
        <div class="notice">
          <strong>In breve.</strong>
          Sostenere un esame e poterlo utilizzare nel percorso che porta alla laurea sono due cose diverse.
          Il piano di studi riguarda la seconda.
        </div>
      </section>
    `,

    approvazione: `
      <details class="piano-accordion">
        <summary>Come avviene l'approvazione?</summary>
        <div class="piano-accordion-body">
          <p>
            La valutazione operativa del piano avviene attraverso CAPS, ma
            <strong>l'approvazione formale spetta al Consiglio di Corso di Studio</strong>.
          </p>

          <div class="piano-flow" aria-label="Iter di approvazione del piano di studi">
            <div class="piano-flow-row">
              <div class="piano-flow-box emphasis"><strong>Presenti il piano in CAPS</strong></div>
            </div>
            <div class="piano-flow-row"><span class="piano-flow-arrow">↓</span></div>
            <div class="piano-flow-row">
              <div class="piano-flow-box"><strong>Valutazione del piano</strong></div>
            </div>
            <div class="piano-flow-row"><span class="piano-flow-arrow">↓</span></div>

            <div class="piano-flow-split">
              <div>
                <div class="piano-flow-box"><strong>Approvato in CAPS</strong></div>
                <div class="piano-flow-row"><span class="piano-flow-arrow">↓</span></div>
                <div class="piano-flow-box emphasis"><strong>Approvazione formale del CdS</strong></div>
              </div>

              <div>
                <div class="piano-flow-box warning"><strong>Da modificare</strong></div>
                <div class="piano-flow-row"><span class="piano-flow-arrow">↓</span></div>
                <div class="piano-flow-box"><strong>Correzione e nuova presentazione</strong></div>
              </div>
            </div>
          </div>

          <div class="notice">
            <strong>Un buon precedente.</strong>
            L'approvazione ottenuta in CAPS non è ancora il momento formale conclusivo,
            ma costituisce un ottimo precedente: in condizioni ordinarie, un piano già valutato positivamente
            in CAPS non viene rimesso in discussione senza motivo dal Consiglio di Corso di Studio.
          </div>

          <aside class="internal-note">
            <strong>Nota interna — da verificare.</strong>
            Precisare meglio, se necessario, chi effettua materialmente la valutazione in CAPS
            e con quale formulazione convenga descrivere il rapporto tra approvazione CAPS e delibera del CdS.
          </aside>
        </div>
      </details>
    `,

    sistemi: `
      <details class="piano-accordion">
        <summary>CAPS e Alice: che differenza c'è?</summary>
        <div class="piano-accordion-body">
          <p>
            <strong>CAPS</strong> è il sistema utilizzato dal Corso di Studio per presentare e valutare il piano di studi.
            <strong>Alice</strong> è invece il sistema amministrativo di Ateneo nel quale viene registrata la carriera.
          </p>
          <p>
            I due sistemi non coincidono necessariamente in tempo reale.
            Per il Corso di Studio, il riferimento per la composizione del percorso è l'ultimo piano approvato.
          </p>

          <aside class="internal-note">
            <strong>Nota interna — da verificare.</strong>
            Precisare quando e come le attività approvate vengono recepite in Alice
            e come vengono gestiti eventuali disallineamenti, soprattutto in prossimità della laurea.
          </aside>
        </div>
      </details>
    `
  };

  document.querySelectorAll("[data-piano-common]").forEach((node) => {
    const key = node.getAttribute("data-piano-common");
    if (blocks[key]) node.innerHTML = blocks[key];
  });
})();
