const { createStrapi } = require('@strapi/strapi');

(async () => {
  try {
    const strapi = await createStrapi().load();
    const attr = strapi.contentType('api::crawl-task.crawl-task').attributes.status;
    console.log(JSON.stringify(attr, null, 2));
    await strapi.destroy();
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  }
})();
