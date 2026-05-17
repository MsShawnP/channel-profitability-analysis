import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const narrative = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/narrative' }),
  schema: z.object({
    title: z.string(),
    order: z.number(),
    section: z.enum([
      'headline',
      'revenue',
      'deductions',
      'fines',
      'operational',
      'trends',
      'contribution',
      'allocation',
    ]),
  }),
});

export const collections = { narrative };
