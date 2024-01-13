"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useEffect, useState } from "react";
import { updateTodoAction } from "@/actions/update-todo";
import { Button } from "../ui/button";
import { TodoSchema } from "@/schemas/todo";
import { useToast } from "../ui/use-toast";
import { useRouter } from "next/navigation";

export default function EditTodoForm({ todo }: { todo: TodoItem }) {
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const form = useForm<z.infer<typeof TodoSchema>>({
    resolver: zodResolver(TodoSchema),
    defaultValues: {
      title: todo.title,
      description: todo.description,
      completed: todo.completed,
    },
  });
  const { toast } = useToast();
  const router = useRouter();
  useEffect(() => {
    form.reset({
      title: todo.title,
      description: todo.description,
      completed: todo.completed,
    });
  }, [todo, form.reset]);

  const onSubmit = async (values: z.infer<typeof TodoSchema>) => {
    try {
      setIsSubmitting(true);
      const data = await updateTodoAction(todo.id, values);
      if (data.error) {
        setSubmitError(data.error);
        throw new Error(data.error);
      }

      if (data.success) {
        setSubmitError("");
        toast({
          title: "Todo Updated",
          description: "Todo Updated Successfully",
        });

        router.push("/dashboard/manage");
      }

    } catch (error) {
      setSubmitError("Failed to update todo");
      toast({
        title: "Failed to Update Todo",
        description: "Request Failed, Try Again",
      });
      setIsSubmitting(false);

      router.push("/dashboard/manage");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {/* Title */}
      <div className="mb-4">
        <label htmlFor="title" className="block mb-2 text-sm font-medium">
          Update Title
        </label>
        <input
          {...form.register("title")}
          id="title"
          type="text"
          className="block w-full rounded-md border border-gray-200 py-2 pl-10 text-sm placeholder:text-gray-500"
          placeholder="Enter Title"
        />
      </div>

      {/* Description */}
      <div className="mb-4">
        <label htmlFor="description" className="block mb-2 text-sm font-medium">
          Update Description
        </label>
        <input
          {...form.register("description")}
          id="description"
          type="text"
          className="block w-full rounded-md border border-gray-200 py-2 pl-10 text-sm placeholder:text-gray-500"
          placeholder="Enter description"
        />
      </div>

      {/* Completed Status */}
      <fieldset className="mb-4">
        <legend className="block mb-2 text-sm font-medium">
          Set the todo status
        </legend>
        <label className="flex items-center gap-2">
          <input
            {...form.register("completed")}
            type="checkbox"
            defaultChecked={todo.completed} // Use defaultChecked for initial value
          />{" "}
          Completed
        </label>
      </fieldset>

      {submitError && <p className="text-red-500">{submitError}</p>}

      <div className="flex justify-end gap-4">
        <Link
          href="/dashboard/manage"
          className="flex h-10 items-center rounded-lg bg-gray-100 px-4 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-200"
        >
          Cancel
        </Link>
        <Button disabled={isSubmitting} type="submit">
          Edit Todo
        </Button>
      </div>
    </form>
  );
}
