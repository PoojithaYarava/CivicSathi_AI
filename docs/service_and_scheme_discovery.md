# Service and Scheme Discovery

Browse uses the existing CSV catalogue via `/api/services` and `/api/schemes`. Search is lexical TF-IDF and can accept catalogue-supported Telugu text; no semantic embedding claim is made. Each record can expose its available description, department, location, eligibility, required documents, direct link, source page, and verification warnings. Detail panels explicitly say when the underlying CSV lacks data.

Most scheme records contain names and links only. The project therefore does not provide an eligibility verdict or compare incomplete schemes. Citizens must confirm eligibility, benefits, and application channels with the official department.

District filtering retains state-level rows but does not imply every state-level service is actually available in each district. Data scope is shown as recorded and should be confirmed with the responsible office.
