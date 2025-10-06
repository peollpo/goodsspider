// @ts-nocheck
import { factories } from '@strapi/strapi';

interface ClaimBody {
  workerId?: string;
  limit?: number;
}

interface CompleteBody {
  state?: 'done' | 'failed';
  result?: Record<string, unknown>;
  errorMessage?: string;
  product?: {
    externalId: string;
    title?: string;
    price?: number | string;
    sales?: number;
    coverUrl?: string;
    metadata?: Record<string, unknown>;
    store?: {
      externalId: string;
      name?: string;
      followers?: number;
      logoUrl?: string;
      metadata?: Record<string, unknown>;
    };
  };
}

type EntityId = number;
const MAX_CLAIM_LIMIT = 20;
const LOCK_TTL_MS = 10 * 60 * 1000;

function normalisePrice(value: number | string | undefined | null): string {
  if (value === undefined || value === null) {
    return '0';
  }
  if (typeof value === 'number') {
    return value.toFixed(2);
  }
  return value;
}

function resolveEntityId(entity: unknown): EntityId | null {
  if (!entity) {
    return null;
  }
  if (typeof entity === 'number') {
    return entity;
  }
  if (typeof entity === 'object' && 'id' in (entity as Record<string, unknown>)) {
    const id = (entity as { id?: number }).id;
    return typeof id === 'number' ? id : null;
  }
  return null;
}

export default factories.createCoreController('api::crawl-task.crawl-task', ({ strapi }) => ({
  async claim(ctx) {
    const body = (ctx.request.body ?? {}) as ClaimBody;
    if (!body.workerId) {
      return ctx.badRequest('workerId is required');
    }

    const limit = Math.min(Math.max(Number(body.limit ?? 1), 1), MAX_CLAIM_LIMIT);
    const now = new Date();
    const staleLock = new Date(now.getTime() - LOCK_TTL_MS).toISOString();

    const pendingTasks = await strapi.entityService.findMany('api::crawl-task.crawl-task', {
      filters: {
        $or: [
          { state: 'pending' },
          {
            state: 'processing',
            lockedAt: { $lt: staleLock },
          },
        ],
      },
      sort: [{ priority: 'desc' }, { createdAt: 'asc' }],
      limit,
    });

    const claimed = [];
    for (const task of pendingTasks) {
      const updated = await strapi.entityService.update('api::crawl-task.crawl-task', task.id, {
        data: {
          state: 'processing',
          workerId: body.workerId,
          lockedAt: now,
          attempts: (task.attempts ?? 0) + 1,
        },
      });
      claimed.push(updated);
    }

    ctx.body = { data: claimed };
  },

  async complete(ctx) {
    const { id } = ctx.params;
    const body = (ctx.request.body ?? {}) as CompleteBody;

    if (!id) {
      return ctx.badRequest('Task id is required');
    }

    const taskId = Number(id);
    const task = await strapi.entityService.findOne('api::crawl-task.crawl-task', taskId, {
      populate: { product: true },
    });

    if (!task) {
      return ctx.notFound('Task not found');
    }

    const nextState = body.state === 'failed' ? 'failed' : 'done';
    const updateData: Record<string, unknown> = {
      state: nextState,
      result: body.result ?? null,
      errorMessage: body.errorMessage ?? null,
      completedAt: new Date(),
      lockedAt: null,
      workerId: null,
    };

    let productId: EntityId | null = resolveEntityId(task.product);

    if (nextState === 'done' && body.product?.externalId) {
      productId = await (this as typeof this).upsertProduct(body.product);
    }

    if (productId) {
      updateData.product = productId;
    }

    const updatedTask = await strapi.entityService.update('api::crawl-task.crawl-task', taskId, {
      data: updateData,
      populate: { product: true },
    });

    ctx.body = { data: updatedTask };
  },

  async upsertStore(storePayload: NonNullable<NonNullable<CompleteBody['product']>['store']> | null): Promise<EntityId | null> {
    if (!storePayload?.externalId) {
      return null;
    }

    const [existing] = await strapi.entityService.findMany('api::store.store', {
      filters: { externalId: storePayload.externalId },
      limit: 1,
    });

    const data = {
      name: storePayload.name ?? existing?.name ?? storePayload.externalId,
      externalId: storePayload.externalId,
      followers: storePayload.followers ?? existing?.followers ?? 0,
      logoUrl: storePayload.logoUrl ?? existing?.logoUrl ?? null,
      metadata: storePayload.metadata ?? existing?.metadata ?? {},
    };

    if (existing) {
      const updated = await strapi.entityService.update('api::store.store', existing.id, {
        data,
      });
      return updated.id;
    }

    const created = await strapi.entityService.create('api::store.store', {
      data,
    });

    return created.id;
  },

  async upsertProduct(productPayload: NonNullable<CompleteBody['product']>): Promise<EntityId> {
    const storeId = await (this as typeof this).upsertStore(productPayload.store ?? null);

    const [existing] = await strapi.entityService.findMany('api::product.product', {
      filters: { externalId: productPayload.externalId },
      limit: 1,
    });

    const existingStoreId = resolveEntityId(existing?.store);
    const data = {
      title: productPayload.title ?? existing?.title ?? productPayload.externalId,
      externalId: productPayload.externalId,
      price: normalisePrice(productPayload.price ?? existing?.price ?? '0'),
      sales: productPayload.sales ?? existing?.sales ?? 0,
      coverUrl: productPayload.coverUrl ?? existing?.coverUrl ?? null,
      metadata: productPayload.metadata ?? existing?.metadata ?? {},
      lastCrawledAt: new Date(),
      store: storeId ?? existingStoreId,
    };

    if (existing) {
      const updated = await strapi.entityService.update('api::product.product', existing.id, {
        data,
      });
      return updated.id;
    }

    const created = await strapi.entityService.create('api::product.product', {
      data,
    });

    return created.id;
  },
}));


