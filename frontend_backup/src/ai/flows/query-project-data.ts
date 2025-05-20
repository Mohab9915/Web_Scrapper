// src/ai/flows/query-project-data.ts
'use server';

/**
 * @fileOverview RAG pipeline for querying scraped data within a specific project.
 *
 * - queryProjectData - A function that handles querying the scraped data using RAG.
 * - QueryProjectDataInput - The input type for the queryProjectData function.
 * - QueryProjectDataOutput - The return type for the queryProjectData function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const QueryProjectDataInputSchema = z.object({
  projectId: z.string().describe('The ID of the project to query.'),
  query: z.string().describe('The question to ask about the scraped data.'),
});
export type QueryProjectDataInput = z.infer<typeof QueryProjectDataInputSchema>;

const QueryProjectDataOutputSchema = z.object({
  answer: z.string().describe('The answer to the question based on the scraped data.'),
  generationCost: z.number().describe('The cost of generating the answer.'),
  sourceDocuments: z
    .array(z.string())
    .describe('The source documents used to generate the answer.'),
});
export type QueryProjectDataOutput = z.infer<typeof QueryProjectDataOutputSchema>;

export async function queryProjectData(input: QueryProjectDataInput): Promise<QueryProjectDataOutput> {
  return queryProjectDataFlow(input);
}

const queryProjectDataPrompt = ai.definePrompt({
  name: 'queryProjectDataPrompt',
  input: {schema: QueryProjectDataInputSchema},
  output: {schema: QueryProjectDataOutputSchema},
  prompt: `You are an expert at answering questions based on scraped data.

  Answer the following question based on the content of the scraped documents associated with project ID {{{projectId}}}.

  Question: {{{query}}}
  `,
});

const queryProjectDataFlow = ai.defineFlow(
  {
    name: 'queryProjectDataFlow',
    inputSchema: QueryProjectDataInputSchema,
    outputSchema: QueryProjectDataOutputSchema,
  },
  async input => {
    const {output} = await queryProjectDataPrompt(input);
    // Here you would integrate with your RAG pipeline to fetch relevant documents
    // and use them to answer the question.
    // For now, we'll just return the prompt output.
    return {
      ...output!,
      generationCost: 0, // Replace with actual cost
      sourceDocuments: [], // Replace with actual source documents
    };
  }
);
