'use server';

/**
 * @fileOverview This file defines a Genkit flow to structure scraped markdown content into a JSON-like table format using an LLM.
 *
 * - structureScrapedData - A function that takes scraped markdown data and attempts to structure it into a JSON format.
 * - StructureScrapedDataInput - The input type for the structureScrapedData function.
 * - StructureScrapedDataOutput - The return type for the structureScrapedData function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const StructureScrapedDataInputSchema = z.object({
  markdownContent: z
    .string()
    .describe('The scraped markdown content to be structured.'),
});
export type StructureScrapedDataInput = z.infer<typeof StructureScrapedDataInputSchema>;

const StructureScrapedDataOutputSchema = z.object({
  structuredData: z
    .string()
    .describe('A JSON-like string representing the structured data.'),
});
export type StructureScrapedDataOutput = z.infer<typeof StructureScrapedDataOutputSchema>;

export async function structureScrapedData(
  input: StructureScrapedDataInput
): Promise<StructureScrapedDataOutput> {
  return structureScrapedDataFlow(input);
}

const prompt = ai.definePrompt({
  name: 'structureScrapedDataPrompt',
  input: {schema: StructureScrapedDataInputSchema},
  output: {schema: StructureScrapedDataOutputSchema},
  prompt: `You are an expert data structuring agent. You will receive markdown content scraped from a website and attempt to structure it into a JSON-like table format. Return a string which is valid JSON.\n\nMarkdown Content:\n{{{markdownContent}}}`,
});

const structureScrapedDataFlow = ai.defineFlow(
  {
    name: 'structureScrapedDataFlow',
    inputSchema: StructureScrapedDataInputSchema,
    outputSchema: StructureScrapedDataOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
